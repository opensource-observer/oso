import { DateTime } from "luxon";
import {
  IEventGroupRecorder,
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
import {
  MultiplexGithubGraphQLRequester,
  MultiplexObjectRetreiver,
} from "./github/multiplex-graphql.js";
import { ArtifactGroupRecorder } from "../recorder/group.js";
import { EnumType } from "json-to-graphql-query";

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

const repositorySummaryRetriever: MultiplexObjectRetreiver<
  GithubRepoLocator
> = (vars) => {
  return {
    type: "repository",
    definition: {
      __args: {
        owner: vars.owner,
        name: vars.repo,
      },
      ...repositoryFollowersAsJson(),
    },
  };
};

function repositoryFollowersAsJson(includeCursor?: boolean) {
  const optional = includeCursor
    ? {
        cursor: new VariableType("cursor"),
      }
    : {};

  return {
    createdAt: true,
    forkCount: true,
    forks: {
      __args: {
        first: 100,
        privacy: new EnumType("PUBLIC"),
        orderBy: {
          field: new EnumType("CREATED_AT"),
          direction: new EnumType("DESC"),
        },
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
          },
        },
      },
    },
    watchers: {
      totalCount: true,
    },
    stargazers: {
      __args: _.merge(
        {
          first: 100,
          orderBy: {
            field: new EnumType("STARRED_AT"),
            direction: new EnumType("DESC"),
          },
        },
        optional,
      ),
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
      },
    },
  };
}

type StarringWrapper = {
  starring: Starring;
  summary: RepoFollowingSummarySingleQueryResponse;
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

type RepoFollowingSummaryResponse = {
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

type RepoFollowingSummarySingleQueryResponse = GithubGraphQLResponse<{
  repository: RepoFollowingSummaryResponse;
}>;

type RepoFollowingSummariesResponse = GithubGraphQLResponse<{
  [key: string]: RepoFollowingSummaryResponse;
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

    const groupRecorder = new ArtifactGroupRecorder(this.recorder);
    // load the summaries for each
    //logger.debug(`loading events for ${repo.name}`);
    try {
      await this.collectEventsForRepo(groupRecorder, artifacts, range);
      committer.commitGroup(groupRecorder);
    } catch (err) {
      committer.failAll(err);
    }
    logger.debug(`follower collection complete`);
  }

  private async collectEventsForRepo(
    groupRecorder: IEventGroupRecorder<Artifact>,
    repos: Artifact[],
    range: Range,
  ) {
    const locators = repos.map((r) => this.splitGithubRepoIntoLocator(r));
    logger.debug("loading summary of many repos");
    const summaries = await this.loadSummaryForRepos(locators);

    if (!summaries) {
      logger.debug("no responses? this is not expected");
      return [];
    }

    for (let i = 0; i < summaries.length; i++) {
      const repo = repos[i];
      const summary = summaries[i];
      const locator = locators[i];
      const ranges = this.rangeOfRepoFollowingSummaryResponse(summary);

      if (
        ranges.forksRange &&
        doRangesIntersect(ranges.forksRange, range, true)
      ) {
        // Gather fork events within this range
        await this.recordForkEvents(
          groupRecorder,
          repo,
          locator,
          summary.forkCount,
          range,
        );
      }
      if (
        ranges.stargazersRange &&
        doRangesIntersect(ranges.stargazersRange, range, true)
      ) {
        // Gather starring events within this range
        await this.recordStarHistoryForRepo(
          groupRecorder,
          repo,
          locator,
          range,
        );
      }
    }
  }

  private async loadSummaryForRepos(
    locators: GithubRepoLocator[],
  ): Promise<RepoFollowingSummaryResponse[]> {
    const multiplex = new MultiplexGithubGraphQLRequester<
      GithubRepoLocator,
      RepoFollowingSummaryResponse
    >(
      "getRepoFollowingSummaries",
      {
        owner: "String!",
        repo: "String!",
      },
      repositorySummaryRetriever,
    );
    try {
      const response = await this.rateLimitedGraphQLGeneratedRequest<
        GithubRepoLocator,
        RepoFollowingSummaryResponse,
        RepoFollowingSummariesResponse
      >(multiplex, locators);
      return response.items;
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
          throw new Error("something is broken");
        }
      }
      throw err;
    }
  }

  private async recordStarHistoryForRepo(
    groupRecorder: IEventGroupRecorder<Artifact>,
    artifact: Artifact,
    locator: GithubRepoLocator,
    range: Range,
  ) {
    let aggregateStatsRecorded = false;

    for await (const { summary, starring } of this.loadStarHistoryForRepo(
      locator,
      range,
    )) {
      if (!aggregateStatsRecorded) {
        // Hack to make this work. we need to change how this works
        await this.recordStarAggregateStats(groupRecorder, locator, summary);
        logger.debug("record watchers");

        await this.recordWatcherEvents(groupRecorder, locator, summary);
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

      await groupRecorder.record(event);
    }
  }

  private async *loadStarHistoryForRepo(
    locator: GithubRepoLocator,
    range: Range,
  ): AsyncGenerator<StarringWrapper> {
    const iterator =
      unpaginateIterator<RepoFollowingSummarySingleQueryResponse>()(
        REPOSITORY_FOLLOWING_SUMMARY,
        "repository.stargazers.edges",
        "repository.stargazers.pageInfo",
        {
          owner: locator.owner,
          name: locator.repo,
        },
      );
    for await (const data of iterator) {
      const response = data.raw as RepoFollowingSummarySingleQueryResponse;

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
    const stargazersCount = res.stargazers.edges.length;
    const forksCount = res.forks.edges.length;
    if (stargazersCount === 0 && forksCount === 0) {
      return {
        stargazersRange: undefined,
        forksRange: undefined,
      };
    }
    let stargazersRange: Range | undefined = undefined;
    let forksRange: Range | undefined = undefined;
    if (stargazersCount > 0) {
      const first = res.stargazers.edges[0];
      const last = res.stargazers.edges.slice(-1)[0];

      stargazersRange = rangeFromISO(last.starredAt, first.starredAt);
    }
    if (forksCount > 0) {
      const first = res.forks.edges[0];
      const last = res.forks.edges.slice(-1)[0];
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
    groupRecorder: IEventGroupRecorder<Artifact>,
    repo: GithubRepoLocator,
    response: RepoFollowingSummarySingleQueryResponse,
  ) {
    const artifact: IncompleteArtifact = {
      name: `${repo.owner}/${repo.repo}`,
      type: ArtifactType.GIT_REPOSITORY,
      namespace: ArtifactNamespace.GITHUB,
    };
    const startOfDay = DateTime.now().startOf("day");
    const starCount = response.repository.stargazers.totalCount;

    return groupRecorder.record({
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

  private async recordWatcherEvents(
    groupRecorder: IEventGroupRecorder<Artifact>,
    repo: GithubRepoLocator,
    response: RepoFollowingSummarySingleQueryResponse,
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
    await groupRecorder.record({
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
    groupRecorder: IEventGroupRecorder<Artifact>,
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
