import { DateTime } from "luxon";
import {
  IEventRecorder,
  IncompleteArtifact,
  IncompleteEvent,
} from "../../../recorder/types.js";
import { logger } from "../../../utils/logger.js";
import { gql } from "graphql-request";
import {
  GithubGraphQLResponse,
  Actor,
  PaginatableEdges,
  GraphQLNode,
  GithubByProjectBaseCollector,
  GithubBaseCollectorOptions,
  GithubRepoLocator,
} from "./common.js";
import { unpaginateIterator } from "../../../events/github/unpaginate.js";
import {
  Project,
  ArtifactNamespace,
  ArtifactType,
  EventType,
  Artifact,
} from "../../../db/orm-entities.js";
import { Repository } from "typeorm";
import { TimeSeriesCacheWrapper } from "../../../cacher/time-series.js";
import _ from "lodash";
import { IArtifactGroup } from "../../../scheduler/types.js";
import {
  Range,
  doRangesIntersect,
  rangeFromISO,
} from "../../../utils/ranges.js";
import { generateSourceIdFromArray } from "../../../utils/source-ids.js";

const GET_ALL_PUBLIC_FORKS = gql`
  query getAllPublicForks($owner: String!, $name: String!, $cursor: String) {
    repository(owner: $owner, name: $name) {
      forks(
        first: 100
        privacy: PUBLIC
        orderBy: { field: CREATED_AT, direction: DESC }
        after: $cursor
      ) {
        totalCount
        pageInfo {
          hasNextPage
          endCursor
        }
        edges {
          node {
            id
            url
            createdAt
            owner {
              __typename
              login
            }
          }
        }
      }
    }
    rateLimit {
      limit
      cost
      remaining
      resetAt
    }
  }
`;

const REPOSITORY_FOLLOWING_SUMMARY = gql`
  query repositoryFollowingSummary(
    $owner: String!
    $name: String!
    $cursor: String
  ) {
    repository(owner: $owner, name: $name) {
      createdAt
      forkCount
      forks(
        first: 100
        privacy: PUBLIC
        orderBy: { field: CREATED_AT, direction: DESC }
      ) {
        totalCount
        pageInfo {
          hasNextPage
          endCursor
        }
        edges {
          node {
            id
            url
            createdAt
            owner {
              __typename
              login
            }
          }
        }
      }
      watchers(first: 1) {
        totalCount
      }
      stargazers(
        first: 100
        after: $cursor
        orderBy: { field: STARRED_AT, direction: DESC }
      ) {
        pageInfo {
          hasNextPage
          endCursor
        }
        totalCount
        edges {
          node {
            login
          }
          starredAt
        }
      }
    }
    rateLimit {
      limit
      cost
      remaining
      resetAt
    }
  }
`;

type StarringWrapper = {
  starring: Starring;
  summary: RepoFollowingSummaryResponse;
};

type Starring = {
  node: Actor;
  starredAt: string;
};

type Fork = {
  id: string;
  url: string;
  createdAt: string;
  owner: Actor & { __typename: string };
};

type RepoFollowingSummaryResponse = GithubGraphQLResponse<{
  repository: {
    createdAt: string;

    // This gives us total forks (the assumption is that this is different than
    // forks.totalCount because of private forking)
    forkCount: number;

    forks: PaginatableEdges<GraphQLNode<Fork>> & {
      totalCount: number;
    };

    watchers: {
      totalCount: number;
    };

    stargazers: PaginatableEdges<Starring> & {
      totalCount: number;
    };
  };
}>;

type GetAllPublicForks = GithubGraphQLResponse<{
  repository: {
    createdAt: string;

    // This gives us total forks (the assumption is that this is different than
    // forks.totalCount because of private forking)
    forkCount: number;

    forks: PaginatableEdges<GraphQLNode<Fork>> & {
      totalCount: number;
    };
  };
}>;

const DefaultGithubFollowingCollectorOptions: GithubBaseCollectorOptions = {
  cacheOptions: {
    bucket: "github-followers",
  },
};

export class GithubFollowingCollector extends GithubByProjectBaseCollector {
  constructor(
    projectRepository: Repository<Project>,
    recorder: IEventRecorder,
    cache: TimeSeriesCacheWrapper,
    options?: Partial<GithubBaseCollectorOptions>,
  ) {
    super(
      projectRepository,
      recorder,
      cache,
      _.merge(DefaultGithubFollowingCollectorOptions, options),
    );
  }

  async collect(
    group: IArtifactGroup<Project>,
    range: Range,
    commitArtifact: (artifact: Artifact | Artifact[]) => Promise<void>,
  ): Promise<void> {
    const project = await group.meta();
    const artifacts = await group.artifacts();
    logger.debug(`collecting followers for repos of Project[${project.slug}]`);

    const recordPromises: Promise<string>[] = [];

    // load the summaries for each
    for (const repo of artifacts) {
      const locator = this.splitGithubRepoIntoLocator(repo);
      const summary = await this.loadSummaryForRepo(locator);
      const ranges = this.rangeOfRepoFollowingSummaryResponse(summary);

      if (
        ranges.forksRange &&
        doRangesIntersect(ranges.forksRange, range, true)
      ) {
        // Gather fork events within this range
        recordPromises.push(
          ...(await this.recordForkEvents(
            repo,
            locator,
            summary.repository.forkCount,
            range,
          )),
        );
      }
      if (
        ranges.stargazersRange &&
        doRangesIntersect(ranges.stargazersRange, range, true)
      ) {
        // Gather starring events within this range
        recordPromises.push(
          ...(await this.recordStarHistoryForRepo(repo, locator, range)),
        );
      }
      await Promise.all([...recordPromises, commitArtifact(repo)]);
    }
  }

  private async loadSummaryForRepo(locator: GithubRepoLocator) {
    return await this.rateLimitedGraphQLRequest<RepoFollowingSummaryResponse>(
      REPOSITORY_FOLLOWING_SUMMARY,
      {
        owner: locator.owner,
        name: locator.repo,
      },
    );
  }

  private async recordStarHistoryForRepo(
    artifact: Artifact,
    locator: GithubRepoLocator,
    range: Range,
  ): Promise<Promise<string>[]> {
    const recordPromises: Promise<string>[] = [];
    let aggregateStatsRecorded = false;

    for await (const { summary, starring } of this.loadStarHistoryForRepo(
      locator,
      range,
    )) {
      if (!aggregateStatsRecorded) {
        // Hack to make this work. we need to change how this works
        recordPromises.push(this.recordStarAggregateStats(locator, summary));
        logger.debug("record watchers");

        recordPromises.push(this.recordWatcherEvents(locator, summary));
        aggregateStatsRecorded = true;
      }
      const commitTime = DateTime.fromISO(starring.starredAt);

      const contributor =
        starring.node && starring.node.login !== ""
          ? {
              name: starring.node.login,
              namespace: ArtifactNamespace.GITHUB,
              type: ArtifactType.GITHUB_USER,
            }
          : undefined;

      const event: IncompleteEvent = {
        time: commitTime,
        type: EventType.STARRED,
        to: artifact,
        from: contributor,
        amount: 0,
        sourceId: generateSourceIdFromArray([
          "STARRED",
          commitTime.toISO()!,
          locator.owner,
          locator.repo,
          contributor?.name || "",
        ]),
      };

      recordPromises.push(this.recorder.record(event));
    }
    return recordPromises;
  }

  private async *loadStarHistoryForRepo(
    locator: GithubRepoLocator,
    range: Range,
  ): AsyncGenerator<StarringWrapper> {
    const iterator = unpaginateIterator<RepoFollowingSummaryResponse>()(
      REPOSITORY_FOLLOWING_SUMMARY,
      "repository.stargazers.edges",
      "repository.stargazers.pageInfo",
      {
        owner: locator.owner,
        name: locator.repo,
      },
    );
    for await (const data of iterator) {
      const response = data.raw as RepoFollowingSummaryResponse;

      for (const starring of data.results) {
        const commitTime = DateTime.fromISO(starring.starredAt);

        if (commitTime.toUnixInteger() < range.startDate.toUnixInteger()) {
          // Once we've reached a commitTime _before_ the range we're searching
          // for, we can stop collecting stars for this artifact.
          return;
        }
        yield {
          starring: starring,
          summary: response,
        };
      }
    }
  }

  private rangeOfRepoFollowingSummaryResponse(
    res: RepoFollowingSummaryResponse,
  ) {
    const stargazersCount = res.repository.stargazers.edges.length;
    const forksCount = res.repository.forks.edges.length;
    if (stargazersCount === 0 && forksCount === 0) {
      return {
        stargazersRange: undefined,
        forksRange: undefined,
      };
    }
    let stargazersRange: Range | undefined = undefined;
    let forksRange: Range | undefined = undefined;
    if (stargazersCount > 0) {
      const first = res.repository.stargazers.edges[0];
      const last = res.repository.stargazers.edges.slice(-1)[0];

      stargazersRange = rangeFromISO(last.starredAt, first.starredAt);
    }
    if (forksCount > 0) {
      const first = res.repository.forks.edges[0];
      const last = res.repository.forks.edges.slice(-1)[0];
      forksRange = rangeFromISO(last.node.createdAt, first.node.createdAt);
    }
    return {
      stargazersRange,
      forksRange,
    };
  }

  private async *loadAllForksHistory(
    repo: GithubRepoLocator,
    range: Range,
  ): AsyncGenerator<Fork> {
    const iterator = unpaginateIterator<GetAllPublicForks>()(
      GET_ALL_PUBLIC_FORKS,
      "repository.forks.edges",
      "repository.forks.pageInfo",
      {
        owner: repo.owner,
        name: repo.repo,
      },
    );
    for await (const data of iterator) {
      for (const fork of data.results) {
        const createdAt = DateTime.fromISO(fork.node.createdAt);

        if (createdAt.toUnixInteger() < range.startDate.toUnixInteger()) {
          return;
        }
        yield fork.node;
      }
    }
  }

  private recordStarAggregateStats(
    repo: GithubRepoLocator,
    response: RepoFollowingSummaryResponse,
  ) {
    const artifact: IncompleteArtifact = {
      name: `${repo.owner}/${repo.repo}`,
      type: ArtifactType.GIT_REPOSITORY,
      namespace: ArtifactNamespace.GITHUB,
    };
    const startOfDay = DateTime.now().startOf("day");
    const starCount = response.repository.stargazers.totalCount;

    return this.recorder.record({
      time: startOfDay,
      type: EventType.STAR_AGGREGATE_STATS,
      to: artifact,
      amount: starCount,
      sourceId: generateSourceIdFromArray([
        "STARS",
        startOfDay.toISO()!,
        repo.owner,
        repo.repo,
      ]),
    });
  }

  private recordWatcherEvents(
    repo: GithubRepoLocator,
    response: RepoFollowingSummaryResponse,
  ) {
    const artifact: IncompleteArtifact = {
      name: `${repo.owner}/${repo.repo}`,
      type: ArtifactType.GIT_REPOSITORY,
      namespace: ArtifactNamespace.GITHUB,
    };
    const startOfDay = DateTime.now().startOf("day");
    const watchersCount = response.repository.watchers.totalCount;

    logger.debug("recording watcher stats for today");

    // Get the aggregate stats for forking
    return this.recorder.record({
      time: startOfDay,
      type: EventType.WATCHER_AGGREGATE_STATS,
      to: artifact,
      amount: watchersCount,
      sourceId: generateSourceIdFromArray([
        "WATCHERS",
        startOfDay.toISO()!,
        repo.owner,
        repo.repo,
      ]),
    });
  }

  private async recordForkEvents(
    artifact: Artifact,
    repo: GithubRepoLocator,
    forkCount: number,
    range: Range,
  ) {
    const startOfDay = DateTime.now().startOf("day");

    const recordPromises: Promise<string>[] = [];

    // Get the aggregate stats for forking
    recordPromises.push(
      this.recorder.record({
        time: startOfDay,
        type: EventType.FORK_AGGREGATE_STATS,
        to: artifact,
        amount: forkCount,
        sourceId: generateSourceIdFromArray([
          "FORKS",
          startOfDay.toISO()!,
          repo.owner,
          repo.repo,
        ]),
      }),
    );

    const recordForkedEvent = (f: Fork) => {
      const createdAt = DateTime.fromISO(f.createdAt);
      const contributor = {
        name: f.owner.login,
        namespace: ArtifactNamespace.GITHUB,
        type:
          f.owner.__typename == "Organization"
            ? ArtifactType.GITHUB_ORG
            : ArtifactType.GITHUB_USER,
      };
      return this.recorder.record({
        time: createdAt,
        type: EventType.FORKED,
        to: artifact,
        from: contributor,
        amount: 0,
        sourceId: f.id,
      });
    };

    // If we have more forks than 100 we need to make some additional queries to gather information
    logger.debug("loading fork history");
    for await (const fork of this.loadAllForksHistory(repo, range)) {
      recordPromises.push(recordForkedEvent(fork));
    }

    return recordPromises;
  }
}
