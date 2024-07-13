import re
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Iterable, TypedDict, cast, ParamSpec, Any
from pathlib import Path

import httpx
import hishel
import dlt
import redis
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

from oso_dagster import constants

GH_URL_RE = re.compile(
    r"^https?://github\.com/(?P<owner>[^/]+)(/(?P<repository>[^/]*))?/?$"
)


class GithubURLType(Enum):
    REPOSITORY = 1
    ENTITY = 2


@dataclass(kw_only=True)
class ParsedGithubURL:
    url: str
    owner: str
    repository: Optional[str] = None
    type: GithubURLType


class Repository(BaseModel):
    id: int
    node_id: str
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


logger = logging.getLogger(__name__)


def gh_repository_to_repository(
    repo: MinimalRepository | FullRepository,
) -> Repository:
    license_spdx_id: str = ""
    license_name: str = ""
    if repo.license_:
        l = cast(MinimalRepositoryPropLicense, repo.license_).model_dump()
        license_spdx_id = l.get("spdx_id", "")
        license_name = l.get("name", "")

    return Repository(
        id=repo.id,
        node_id=repo.node_id,
        name_with_owner=repo.full_name,
        name=repo.name,
        branch=repo.default_branch or "main",
        star_count=repo.stargazers_count or 0,
        watcher_count=repo.watchers_count or 0,
        fork_count=repo.forks_count or 0,
        license_name=license_name,
        license_spdx_id=license_spdx_id,
        url=repo.html_url,
        is_fork=repo.fork,
        language=repo.language or "",
    )


class GithubRepositoryResolver:
    def __init__(self, gh: GitHub):
        self._gh = gh

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
                yield gh_repository_to_repository(repo)
        except:
            repos = self.get_repos_for_user(parsed)
            for repo in repos:
                yield gh_repository_to_repository(repo)

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
        return [gh_repository_to_repository(repo.parsed_data)]

    def parse_url(self, url: str) -> ParsedGithubURL:
        match = GH_URL_RE.match(url)
        if not match:
            raise InvalidGithubURL(
                f"{url} is not a valid github repository, user, or organization url"
            )
        if match.group("repository"):
            return ParsedGithubURL(
                url=url,
                owner=match.group("owner"),
                repository=match.group("repository"),
                type=GithubURLType.REPOSITORY,
            )
        return ParsedGithubURL(
            url=url,
            owner=match.group("owner"),
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


@dlt.resource(
    name="repositories",
    table_name="repositories",
    columns=pydantic_to_table_schema_columns(Repository),
    write_disposition="merge",
    primary_key="id",
    merge_key="node_id",
)
def oss_directory_github_repositories_resource(
    projects_df: pl.DataFrame, gh_token: str = dlt.secrets.value
):
    """Based on the oss_directory data we resolve repositories"""
    logger.debug("starting github repo resolver")

    if constants.redis_cache:
        gh = CachedGithub(
            gh_token,
            sync_storage=hishel.RedisStorage(
                client=redis.Redis(
                    constants.redis_cache,
                ),
                ttl=3600,
            ),
        )
    else:
        gh = GitHub(gh_token)

    resolver = GithubRepositoryResolver(gh)
    for repo in resolver.resolve_repos(projects_df):
        yield repo


@dlt.source
def oss_directory_github_repositories():
    return oss_directory_github_repositories_resource
