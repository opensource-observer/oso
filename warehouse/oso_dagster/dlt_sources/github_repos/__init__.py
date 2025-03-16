import logging
import typing as t
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from functools import partial, wraps
from urllib.parse import ParseResult, urlparse

import arrow
import dlt
import hishel
import httpx
import polars as pl
from githubkit import GitHub
from githubkit.exception import RequestFailed
from githubkit.retry import RetryChainDecision, RetryRateLimit, RetryServerError
from githubkit.versions.latest.models import (
    FullRepository,
    MinimalRepository,
    MinimalRepositoryPropLicense,
)
from oso_dagster.factories.dlt import pydantic_to_dlt_nullable_columns
from oso_dagster.utils import (
    ParallelizeConfig,
    dlt_parallelize,
    get_async_http_cache_storage,
    get_sync_http_cache_storage,
)
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


class GithubURLType(Enum):
    REPOSITORY = 1
    ENTITY = 2


@dataclass(kw_only=True)
class ParsedGithubURL:
    parsed_url: ParseResult
    url: str
    owner: str
    repository: t.Optional[str] = None
    type: GithubURLType


class Repository(BaseModel):
    ingestion_time: t.Optional[datetime]
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


class GithubRepositorySBOMItem(BaseModel):
    artifact_namespace: str
    artifact_name: str
    artifact_source: str
    package: str
    package_source: str
    package_version: t.Optional[str]
    snapshot_at: datetime


class GithubClientConfig(BaseModel):
    gh_token: str
    rate_limit_max_retry: int = 5
    server_error_max_rety: int = 3
    http_cache: t.Optional[str] = None


class InvalidGithubURL(Exception):
    pass


class GithubRepositoryResolverRequest:
    def __init__(self, gh: GitHub):
        pass


class CachedGithub(GitHub):
    """This configures the github sdk with a caching system of our choice"""

    def __init__(
        self,
        auth: t.Any = None,
        sync_storage: t.Optional[hishel.BaseStorage] = None,
        async_storage: t.Optional[hishel.AsyncBaseStorage] = None,
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
        l = t.cast(MinimalRepositoryPropLicense, repo.license_).model_dump()
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

    async def get_repos_for_url(self, url: str) -> t.List[Repository]:
        logger.debug(f"Getting repos for {url}")
        parsed = self.parse_url(url)
        match parsed.type:
            case GithubURLType.ENTITY:
                return await self.get_repos_for_entity(parsed)
            case GithubURLType.REPOSITORY:
                return await self.get_repo(parsed)

    async def get_repos_for_entity(self, parsed: ParsedGithubURL) -> t.List[Repository]:
        try:
            repos = await self.get_repos_for_org(parsed)
            return [
                gh_repository_to_repository(self._ingestion_time, repo)
                for repo in repos
            ]
        except RequestFailed:
            repos = await self.get_repos_for_user(parsed)
            return [
                gh_repository_to_repository(self._ingestion_time, repo)
                for repo in repos
            ]

    async def get_repos_for_org(self, parsed: ParsedGithubURL) -> t.List:
        headers = {"X-Github-Next-Global-ID": "1"}
        repo_list = []

        async for repo in self._gh.paginate(
            self._gh.rest.repos.async_list_for_org,
            org=parsed.owner,
            headers=headers,
        ):
            repo_list.append(repo)

        return repo_list

    async def get_repos_for_user(self, parsed: ParsedGithubURL) -> t.List:
        headers = {"X-Github-Next-Global-ID": "1"}
        repo_list = []

        async for repo in self._gh.paginate(
            self._gh.rest.repos.async_list_for_user,
            username=parsed.owner,
            headers=headers,
        ):
            repo_list.append(repo)

        return repo_list

    async def get_repo(self, parsed: ParsedGithubURL) -> t.List[Repository]:
        if not parsed.repository:
            raise Exception("Repository must be set")

        try:
            repo = await self._gh.rest.repos.async_get(
                owner=parsed.owner,
                repo=parsed.repository,
                headers={"X-Github-Next-Global-ID": "1"},
            )
            return [gh_repository_to_repository(self._ingestion_time, repo.parsed_data)]
        except RequestFailed as e:
            if e.response.status_code == 404:
                logger.warning(f"skipping {parsed.url}. not found")
                return []
            else:
                raise e

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

    async def get_sbom_for_repo(
        self, owner: str, name: str
    ) -> t.List[GithubRepositorySBOMItem]:
        try:
            sbom = await self._gh.rest.dependency_graph.async_export_sbom(
                owner,
                name,
            )
            logger.debug("Got SBOM for %s", f"{owner}/{name}")
            graph = sbom.parsed_data.sbom
            sbom_list: t.List[GithubRepositorySBOMItem] = []

            for package in graph.packages:
                if not package.external_refs:
                    logger.warning(
                        "Skipping %s for sbom %s, no external refs found",
                        f"{package.name}",
                        f"{owner}/{name}",
                    )
                    continue

                package_locator = package.external_refs[0].reference_locator
                package_source = package_locator[
                    len("pkg:") : package_locator.index("/")
                ]
                package_name = package.name or "UNKNOWN"

                sbom_list.append(
                    GithubRepositorySBOMItem(
                        artifact_namespace=owner,
                        artifact_name=name,
                        artifact_source="GITHUB",
                        package=package_name,
                        package_source=package_source.upper(),
                        package_version=package.version_info or None,
                        snapshot_at=arrow.get(graph.creation_info.created).datetime,
                    )
                )

            return sbom_list
        except RequestFailed as exception:
            if exception.response.status_code == 404:
                logger.warning("Skipping %s, no SBOM found", f"{owner}/{name}")
            else:
                logger.error("Error getting SBOM: %s", exception)
            return []
        except ValidationError as exception:
            validation_errors = [
                f"{error['loc'][0]}: {error['msg']}" for error in exception.errors()
            ]
            logger.warning(
                "Skipping %s, SBOM is malformed: %s",
                f"{owner}/{name}",
                ", ".join(validation_errors),
            )
            return []

    @staticmethod
    def get_github_client(config: GithubClientConfig) -> GitHub:
        if config.http_cache:
            logger.debug("Using the cache at: %s", config.http_cache)
            return CachedGithub(
                config.gh_token,
                sync_storage=get_sync_http_cache_storage(config.http_cache),
                async_storage=get_async_http_cache_storage(config.http_cache),
                auto_retry=RetryChainDecision(
                    RetryRateLimit(max_retry=config.rate_limit_max_retry),
                    RetryServerError(max_retry=config.server_error_max_rety),
                ),
            )
        logger.debug("Loading github client without a cache")
        return GitHub(
            config.gh_token,
            auto_retry=RetryChainDecision(
                RetryRateLimit(max_retry=config.rate_limit_max_retry),
                RetryServerError(max_retry=config.server_error_max_rety),
            ),
        )

    def safe_parse_url(self, url: str) -> ParsedGithubURL | None:
        try:
            return self.parse_url(url)
        except InvalidGithubURL as e:
            logger.warning("Skipping invalid url %s: %s", url, e)
            return None


def with_progress_logger(
    funcs_gen: t.Generator[t.Callable, None, None],
    log_interval_pct: int = 5,
) -> t.List[t.Callable]:
    """Wraps functions at specific percentage points with logging."""

    funcs_list = list(funcs_gen)

    total = len(funcs_list)
    if total == 0:
        return []

    logger.info(f"ProgressLogging: Starting processing of {total} items")

    positions_to_log: t.List[int] = []

    for p in range(0, 101, log_interval_pct):
        pos = int(p * total / 100)
        if pos < total:
            positions_to_log.append(pos)

    if positions_to_log[-1] != total - 1:
        positions_to_log.append(total - 1)

    def create_wrapper(orig_func: t.Callable, position: int, pct: int) -> t.Callable:
        @wraps(orig_func)
        async def wrapped():
            logger.info(f"ProgressLogging: Processing item {position}/{total} ({pct}%)")
            return await orig_func()

        return wrapped

    for pos in positions_to_log:
        percentage = int((pos / total) * 100)
        original_func = funcs_list[pos]
        funcs_list[pos] = create_wrapper(original_func, pos, percentage)

    return funcs_list


@dlt.resource(
    name="repositories",
    table_name="repositories",
    columns=pydantic_to_dlt_nullable_columns(Repository),
    write_disposition="append",
    primary_key="id",
    merge_key="node_id",
)
@dlt_parallelize(
    ParallelizeConfig(
        chunk_size=16,
        parallel_batches=5,
        wait_interval=45,
    )
)
def oss_directory_github_repositories_resource(
    all_github_urls: t.List[str],
    /,
    gh_token: str = dlt.secrets.value,
    rate_limit_max_retry: int = 5,
    server_error_max_rety: int = 3,
):
    """Based on the oss_directory data we resolve repositories"""

    config = GithubClientConfig(
        gh_token=gh_token,
        rate_limit_max_retry=rate_limit_max_retry,
        server_error_max_rety=server_error_max_rety,
    )

    gh = GithubRepositoryResolver.get_github_client(config)
    resolver = GithubRepositoryResolver(gh)

    funcs = (
        partial(resolver.get_repos_for_url, github_url)
        for github_url in all_github_urls
    )

    yield from with_progress_logger(funcs)


@dlt.resource(
    name="sbom",
    table_name="sbom",
    columns=pydantic_to_dlt_nullable_columns(GithubRepositorySBOMItem),
    write_disposition="append",
)
@dlt_parallelize(
    ParallelizeConfig(
        chunk_size=16,
        parallel_batches=5,
        wait_interval=45,
    )
)
def oss_directory_github_sbom_resource(
    all_repo_urls: t.List[t.Tuple[str, str]],
    /,
    gh_token: str = dlt.secrets.value,
    rate_limit_max_retry: int = 5,
    server_error_max_rety: int = 3,
):
    """Retrieve SBOM information for GitHub repositories"""

    config = GithubClientConfig(
        gh_token=gh_token,
        rate_limit_max_retry=rate_limit_max_retry,
        server_error_max_rety=server_error_max_rety,
    )

    gh = GithubRepositoryResolver.get_github_client(config)
    resolver = GithubRepositoryResolver(gh)

    funcs = (
        partial(resolver.get_sbom_for_repo, owner, repo)
        for owner, repo in all_repo_urls
    )

    yield from with_progress_logger(funcs)
