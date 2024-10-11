import logging
import arrow
from datetime import datetime, UTC
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Iterable, cast, ParamSpec, Any
from pathlib import Path
from urllib.parse import urlparse, ParseResult

import httpx
import hishel
import dlt
from dlt.common.libs.pydantic import pydantic_to_table_schema_columns
import polars as pl
from pydantic import BaseModel
from githubkit import GitHub
from githubkit.exception import RequestFailed
from githubkit.versions.latest.models import (
    MinimalRepository,
    FullRepository,
    MinimalRepositoryPropLicense,
)
from githubkit.retry import RetryRateLimit, RetryChainDecision, RetryServerError


from oso_dagster import constants
from oso_dagster.utils import get_async_http_cache_storage, get_sync_http_cache_storage


logger = logging.getLogger(__name__)


class GithubURLType(Enum):
    REPOSITORY = 1
    ENTITY = 2


@dataclass(kw_only=True)
class ParsedGithubURL:
    parsed_url: ParseResult
    url: str
    owner: str
    repository: Optional[str] = None
    type: GithubURLType


class Repository(BaseModel):
    ingestion_time: Optional[datetime]
    id: int
    node_id: str
    owner: str
    name_with_owner: str
    url: str
    name: str
    is_fork: bool
    branch: str
    fork_count: int
    star_count: int
    watcher_count: int
    license_spdx_id: str
    license_name: str
    language: str
    created_at: datetime
    updated_at: datetime


class InvalidGithubURL(Exception):
    pass


class GithubRepositoryResolverRequest:
    def __init__(self, gh: GitHub):
        pass


class CachedGithub(GitHub):
    """This configures the github sdk with a caching system of our choice"""

    def __init__(
        self,
        auth: Any = None,
        sync_storage: Optional[hishel.BaseStorage] = None,
        async_storage: Optional[hishel.AsyncBaseStorage] = None,
        **kwargs,
    ):
        super().__init__(auth, **kwargs)
        self._cache_sync_storage = sync_storage
        self._cache_async_storage = async_storage

    def _create_sync_client(self) -> httpx.Client:
        if not self._cache_sync_storage:
            return super()._create_sync_client()
        transport = hishel.CacheTransport(
            httpx.HTTPTransport(), storage=self._cache_sync_storage
        )
        return httpx.Client(**self._get_client_defaults(), transport=transport)

    def _create_async_client(self) -> httpx.AsyncClient:
        if not self._cache_async_storage:
            return super()._create_async_client()
        transport = hishel.AsyncCacheTransport(
            httpx.AsyncHTTPTransport(), storage=self._cache_async_storage
        )
        return httpx.AsyncClient(**self._get_client_defaults(), transport=transport)


def gh_repository_to_repository(
    ingestion_time: datetime,
    repo: MinimalRepository | FullRepository,
) -> Repository:
    license_spdx_id: str = ""
    license_name: str = ""
    if repo.license_:
        l = cast(MinimalRepositoryPropLicense, repo.license_).model_dump()
        license_spdx_id = l.get("spdx_id", "")
        license_name = l.get("name", "")

    return Repository(
        ingestion_time=ingestion_time,
        id=repo.id,
        node_id=repo.node_id,
        name_with_owner=repo.full_name,
        name=repo.name,
        owner=repo.owner.login,
        branch=repo.default_branch or "main",
        star_count=repo.stargazers_count or 0,
        watcher_count=repo.watchers_count or 0,
        fork_count=repo.forks_count or 0,
        license_name=license_name,
        license_spdx_id=license_spdx_id,
        url=repo.html_url,
        is_fork=repo.fork,
        language=repo.language or "",
        created_at=repo.created_at or datetime.fromtimestamp(0),
        updated_at=repo.updated_at or datetime.fromtimestamp(0),
    )


class GithubRepositoryResolver:
    def __init__(self, gh: GitHub):
        self._gh = gh
        self._ingestion_time = datetime.now(UTC)

    def resolve_repos(self, projects_df: pl.DataFrame):
        # Unnest all of the urls to get
        # Process all of the urls and resolve repos based on the urls
        urls = self.github_urls_from_df(projects_df)
        logger.debug(f"URLS loaded: {len(urls)}")
        for url in urls["url"]:
            if not url:
                continue

            logger.debug(f"getting repos for url: {url}")
            try:
                repos = self.get_repos_for_url(url)
            except InvalidGithubURL:
                logger.warn(f"skipping invalid github url: {url}")
                continue

            try:
                for repo in repos:
                    yield repo
            except RequestFailed as e:
                if e.response.status_code == 404:
                    logging.warn(f"skipping {url}. no repos found")
                    continue
                else:
                    raise e

    def get_repos_for_url(self, url: str):
        logger.info(f"Getting repos for {url}")
        parsed = self.parse_url(url)
        match parsed.type:
            case GithubURLType.ENTITY:
                return self.get_repos_for_entity(parsed)
            case GithubURLType.REPOSITORY:
                return self.get_repo(parsed)

    def get_repos_for_entity(self, parsed: ParsedGithubURL) -> Iterable[Repository]:
        try:
            repos = self.get_repos_for_org(parsed)
            for repo in repos:
                yield gh_repository_to_repository(self._ingestion_time, repo)
        except:
            repos = self.get_repos_for_user(parsed)
            for repo in repos:
                yield gh_repository_to_repository(self._ingestion_time, repo)

    def get_repos_for_org(self, parsed: ParsedGithubURL):
        repos = self._gh.paginate(
            self._gh.rest.repos.list_for_org,
            org=parsed.owner,
            headers={"X-Github-Next-Global-ID": "1"},
        )
        return repos

    def get_repos_for_user(self, parsed: ParsedGithubURL):
        repos = self._gh.paginate(
            self._gh.rest.repos.list_for_user,
            username=parsed.owner,
            headers={"X-Github-Next-Global-ID": "1"},
        )
        return repos

    def get_repo(self, parsed: ParsedGithubURL) -> Iterable[Repository]:
        if not parsed.repository:
            raise Exception("Repository must be set")
        try:
            repo = self._gh.rest.repos.get(
                owner=parsed.owner,
                repo=parsed.repository,
                headers={"X-Github-Next-Global-ID": "1"},
            )
        except RequestFailed as e:
            if e.response.status_code == 404:
                logging.warn(f"skipping {parsed.url}. not found")
                return []
            else:
                raise e
        return [gh_repository_to_repository(self._ingestion_time, repo.parsed_data)]

    def parse_url(self, url: str) -> ParsedGithubURL:
        parsed_url = urlparse(url)

        logger.debug(f"parsed url {parsed_url}")

        if parsed_url.netloc != "github.com":
            raise InvalidGithubURL(f"{url} is not a valid github url")

        if not parsed_url.path.startswith("/"):
            raise InvalidGithubURL(f"{url} is not a valid github url")

        # Match the path of the url after the first slash and removing any
        # trailing slashes
        match = parsed_url.path[1:].rstrip("/").split("/")
        if len(match) not in [1, 2]:
            raise InvalidGithubURL(
                f"{url} is not a valid github repository, user, or organization url"
            )
        if len(match) == 2:
            return ParsedGithubURL(
                parsed_url=parsed_url,
                url=url,
                owner=match[0],
                repository=match[1],
                type=GithubURLType.REPOSITORY,
            )
        return ParsedGithubURL(
            parsed_url=parsed_url,
            url=url,
            owner=match[0],
            type=GithubURLType.ENTITY,
        )

    def github_urls_from_df(self, projects_df: pl.DataFrame):
        projects_github = projects_df.select(pl.col("name"), pl.col("github"))
        all_github_urls = (
            projects_github.filter(pl.col("github").is_not_null())["github"]
            .explode()
            .struct.unnest()
        )
        logger.debug(f"unnested all github urls and got {len(all_github_urls)} rows")
        return all_github_urls


def repository_columns():
    table_schema_columns = pydantic_to_table_schema_columns(Repository)
    for column in table_schema_columns.values():
        column["nullable"] = True
    print(table_schema_columns)
    return table_schema_columns


@dlt.resource(
    name="repositories",
    table_name="repositories",
    columns=repository_columns(),
    write_disposition="append",
    primary_key="id",
    merge_key="node_id",
)
def oss_directory_github_repositories_resource(
    projects_df: pl.DataFrame,
    gh_token: str = dlt.secrets.value,
    rate_limit_max_retry: int = 5,
    server_error_max_rety: int = 3,
):
    """Based on the oss_directory data we resolve repositories"""

    if constants.http_cache:
        logger.debug(f"Using the cache at: {constants.http_cache}")
        gh = CachedGithub(
            gh_token,
            sync_storage=get_sync_http_cache_storage(constants.http_cache),
            async_storage=get_async_http_cache_storage(constants.http_cache),
            auto_retry=RetryChainDecision(
                RetryRateLimit(max_retry=rate_limit_max_retry),
                RetryServerError(max_retry=server_error_max_rety),
            ),
        )
    else:
        logger.debug(f"Loading github client without a cache")
        gh = GitHub(
            gh_token,
            auto_retry=RetryChainDecision(
                RetryRateLimit(max_retry=rate_limit_max_retry),
                RetryServerError(max_retry=server_error_max_rety),
            ),
        )

    resolver = GithubRepositoryResolver(gh)
    for repo in resolver.resolve_repos(projects_df):
        yield repo


@dlt.source
def oss_directory_github_repositories():
    return oss_directory_github_repositories_resource
