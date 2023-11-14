import { DateTime } from "luxon";
import {
  IEventRecorderClient,
  IncompleteArtifact,
  IncompleteEvent,
  RecordHandle,
} from "../recorder/types.js";
import { logger } from "../utils/logger.js";
import { gql, ClientError } from "graphql-request";
import {
  GithubGraphQLResponse,
  Actor,
  PaginatableEdges,
  GraphQLNode,
  GithubBaseCollectorOptions,
  GithubRepoLocator,
  GithubBatchedProjectArtifactsBaseCollector,
} from "./github/common.js";
import { unpaginateIterator } from "./github/unpaginate.js";
import {
  Project,
  ArtifactNamespace,
  ArtifactType,
  Artifact,
} from "../db/orm-entities.js";
import { Repository } from "typeorm";
import { TimeSeriesCacheWrapper } from "../cacher/time-series.js";
import _ from "lodash";
import {
  IArtifactGroup,
  IArtifactGroupCommitmentProducer,
} from "../scheduler/types.js";
import { Range, doRangesIntersect, rangeFromISO } from "../utils/ranges.js";
import { sha1FromArray } from "../utils/source-ids.js";
import { GraphQLError } from "graphql";
import { Batch } from "../scheduler/common.js";
import { VariableType } from "json-to-graphql-query";

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

function repositoryFollowersAsJson(includeCursor: boolean) {
  const optional = includeCursor ? {
    cursor: new VariableType('cursor'),
  } : {};

  return {
    createdAt: true,
    forkCount: true,
    forks: {
      __args: {
        first: 100,
        privacy: 'PUBLIC',
        orderBy: { field: 'CREATED_AT', direction: 'DESC' },
      },
      totalCount: true,
      pageInfo: {
        hasNextPage: true,
        endCursor: true,
      },
      edges: {
        node: {
          id: true,
          url: true,
          createdAt: true,
          owner: {
            __typename: true,
            login: true,
          }
        }
      }
    },
    watchers: {
      totalCount: true,
    },
    stargazers: {
      __args: _.merge({
        first: 100,
        orderBy: { field: 'STARRED_AT', direction: 'DESC' },
      }, optional),
      pageInfo: {
        hasNextPage: true,
        endCursor: true,
      },
      totalCount: true,
      edges: {
        node: {
          login: true,
        },
        starredAt: true,
      }
    },
  }
}

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

export class GithubFollowingCollector extends GithubBatchedProjectArtifactsBaseCollector {
  constructor(
    projectRepository: Repository<Project>,
    recorder: IEventRecorderClient,
    cache: TimeSeriesCacheWrapper,
    batchSize: number,
    options?: Partial<GithubBaseCollectorOptions>,
  ) {
    super(
      projectRepository,
      recorder,
      cache,
      batchSize,
      _.merge(DefaultGithubFollowingCollectorOptions, options),
    );
  }

  async collect(
    group: IArtifactGroup<Batch>,
    range: Range,
    committer: IArtifactGroupCommitmentProducer,
  ): Promise<void> {
    const batch = await group.meta();
    const artifacts = await group.artifacts();
    logger.debug(`collecting followers for repos of ${batch.name}`);

    // load the summaries for each
    for (const repo of artifacts) {
      logger.debug(`loading events for ${repo.name}`);
      try {
        const recordPromises = await this.collectEventsForRepo(repo, range);
        committer.commit(repo).withHandles(recordPromises);
      } catch (err) {
        committer.commit(repo).withResults({
          errors: [err],
          success: [],
        });
      }
    }
    logger.debug(`follower collection complete`);
  }

  private async collectEventsForRepo(
    repo: Artifact,
    range: Range,
  ): Promise<RecordHandle[]> {
    const locator = this.splitGithubRepoIntoLocator(repo);
    const summary = await this.loadSummaryForRepo(locator);
    if (!summary) {
      logger.debug(
        `${locator.owner}/${locator.repo} doesn't exist or is empty`,
      );
      return [];
    }
    const ranges = this.rangeOfRepoFollowingSummaryResponse(summary);
    const recordPromises = [];

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
    return recordPromises;
  }

  private async loadSummaryForRepo(
    locator: GithubRepoLocator,
  ): Promise<RepoFollowingSummaryResponse | undefined> {
    try {
      return await this.rateLimitedGraphQLRequest<RepoFollowingSummaryResponse>(
        REPOSITORY_FOLLOWING_SUMMARY,
        {
          owner: locator.owner,
          name: locator.repo,
        },
      );
    } catch (err) {
      if (err instanceof ClientError) {
        const errors = err.response.errors || [];
        const notFoundError = errors.filter((e) => {
          return (
            (e as GraphQLError & { [key: string]: string }).type === "NOT_FOUND"
          );
        });

        // This repo doesn't exist. Just skip.
        if (notFoundError.length > 0) {
          return;
        }
      }
      throw err;
    }
  }

  private async recordStarHistoryForRepo(
    artifact: Artifact,
    locator: GithubRepoLocator,
    range: Range,
  ): Promise<RecordHandle[]> {
    const recordHandles: RecordHandle[] = [];
    let aggregateStatsRecorded = false;

    for await (const { summary, starring } of this.loadStarHistoryForRepo(
      locator,
      range,
    )) {
      if (!aggregateStatsRecorded) {
        // Hack to make this work. we need to change how this works
        recordHandles.push(
          await this.recordStarAggregateStats(locator, summary),
        );
        logger.debug("record watchers");

        recordHandles.push(await this.recordWatcherEvents(locator, summary));
        aggregateStatsRecorded = true;
      }
      const commitTime = DateTime.fromISO(starring.starredAt);

      const contributor =
        starring.node && starring.node.login !== ""
          ? {
            name: starring.node.login.toLowerCase(),
            namespace: ArtifactNamespace.GITHUB,
            type: ArtifactType.GITHUB_USER,
          }
          : undefined;

      const event: IncompleteEvent = {
        time: commitTime,
        type: {
          name: "STARRED",
          version: 1,
        },
        to: artifact,
        from: contributor,
        amount: 1,
        sourceId: sha1FromArray([
          "STARRED",
          commitTime.toISO()!,
          locator.owner,
          locator.repo,
          contributor?.name || "",
        ]),
      };

      recordHandles.push(await this.recorder.record(event));
    }
    return recordHandles;
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
      type: {
        name: "STAR_AGGREGATE_STATS",
        version: 1,
      },
      to: artifact,
      amount: starCount,
      sourceId: sha1FromArray([
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
    const startOfDay = DateTime.now().toUTC().startOf("day");
    const watchersCount = response.repository.watchers.totalCount;

    logger.debug("recording watcher stats for today");

    // Get the aggregate stats for forking
    return this.recorder.record({
      time: startOfDay,
      type: {
        name: "WATCHER_AGGREGATE_STATS",
        version: 1,
      },
      to: artifact,
      amount: watchersCount,
      sourceId: sha1FromArray([
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
    const startOfDay = DateTime.now().toUTC().startOf("day");

    const recordHandles: RecordHandle[] = [];

    // Get the aggregate stats for forking
    recordHandles.push(
      await this.recorder.record({
        time: startOfDay,
        type: {
          name: "FORK_AGGREGATE_STATS",
          version: 1,
        },
        to: artifact,
        amount: forkCount,
        sourceId: sha1FromArray([
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
        type: {
          name: "FORKED",
          version: 1,
        },
        to: artifact,
        from: contributor,
        amount: 1,
        sourceId: f.id,
      });
    };

    // If we have more forks than 100 we need to make some additional queries to gather information
    logger.debug("loading fork history");
    for await (const fork of this.loadAllForksHistory(repo, range)) {
      if (DateTime.fromISO(fork.createdAt) < range.startDate) {
        break;
      }
      recordHandles.push(await recordForkedEvent(fork));
    }

    return recordHandles;
  }
}
