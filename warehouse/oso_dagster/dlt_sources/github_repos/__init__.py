import re
import logging
from dataclasses import dataclass
from pydantic import BaseModel
from enum import Enum
from typing import Optional, Iterable, TypedDict, cast

from githubkit import GitHub
from githubkit.exception import RequestFailed
from githubkit.versions.latest.models import (
    MinimalRepository,
    FullRepository,
    MinimalRepositoryPropLicense,
)

import polars as pl
import dlt

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


class BranchRef(BaseModel):
    name: str


class License(BaseModel):
    name: str
    spdx_id: str


class Repository(BaseModel):
    id: int
    node_id: str
    name_with_owner: str
    url: str
    name: str
    is_fork: bool
    default_branch_ref: Optional[BranchRef] = None
    fork_count: int
    star_count: int
    watcher_count: int
    license: Optional[License] = None
    language: str


class InvalidGithubURL(Exception):
    pass


class GithubRepositoryResolverRequest:
    def __init__(self, gh: GitHub):
        pass


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def gh_repository_to_repository(
    repo: MinimalRepository | FullRepository,
) -> Repository:
    license: Optional[License] = None
    if repo.license_:
        l = cast(MinimalRepositoryPropLicense, repo.license_).model_dump()
        license = License(spdx_id=l.get("spdx_id", ""), name=l.get("name", ""))

    return Repository(
        id=repo.id,
        node_id=repo.node_id,
        name_with_owner=repo.full_name,
        name=repo.name,
        default_branch_ref=BranchRef(name=repo.default_branch or "main"),
        star_count=repo.stargazers_count or 0,
        watcher_count=repo.watchers_count or 0,
        fork_count=repo.forks_count or 0,
        license=license,
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
        print(f"URLS loaded: {len(urls)}")
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


@dlt.resource(table_name="repositories", columns=Repository)  # type: ignore
def oss_directory_github_repositories_resource(
    projects_df: pl.DataFrame, gh_token: str = dlt.secrets.value
):
    """Based on the oss_directory data we resolve repositories"""
    logger.debug("starting github repo resolver")
    gh = GitHub(gh_token)

    resolver = GithubRepositoryResolver(gh)
    for repo in resolver.resolve_repos(projects_df):
        yield repo


@dlt.source
def oss_directory_github_repositories():
    return oss_directory_github_repositories_resource
