import { DateTime } from "luxon";
import {
  IEventRecorder,
  IncompleteArtifact,
  IncompleteEvent,
} from "../../../recorder/types.js";
import {
  ArtifactNamespace,
  ArtifactType,
  ContributorNamespace,
  EventType,
  PrismaClient,
} from "@prisma/client";
import { BatchEventRecorder } from "../../../recorder/recorder.js";
import { prisma as prismaClient } from "../../../db/prisma-client.js";
import { logger } from "../../../utils/logger.js";
import { CommonArgs } from "../../../utils/api.js";
import { gql } from "graphql-request";
import {
  GithubGraphQLResponse,
  Actor,
  PaginatableEdges,
  GraphQLNode,
} from "./common.js";
import {
  unpaginateIterator,
  PageInfo,
} from "../../../events/github/unpaginate.js";

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

type GithubRepoLocator = { owner: string; repo: string };

export class GithubFollowingFetcher {
  private recorder: IEventRecorder;
  private prisma: PrismaClient;

  constructor(prisma: PrismaClient, recorder: IEventRecorder) {
    this.prisma = prisma;
    this.recorder = recorder;
  }

  async run() {
    this.recorder.setActorScope(
      [ArtifactNamespace.GITHUB],
      [ContributorNamespace.GITHUB_USER, ContributorNamespace.GITHUB_ORG],
    );

    const repos = await this.loadRelevantRepos();

    for (const repo of repos) {
      await this.recordEventsForRepo(repo);
    }

    // Report that we've completed the job
    await this.recorder.waitAll();
  }

  private async loadRelevantRepos(): Promise<GithubRepoLocator[]> {
    const projects = await this.prisma.project.findMany({
      where: {
        name: {
          in: ["0xSplits", "Safe", "Uniswap"],
        },
      },
      include: {
        artifacts: {
          include: {
            artifact: true,
          },
          where: {
            artifact: {
              namespace: {
                in: [ArtifactNamespace.GITHUB],
              },
            },
          },
        },
      },
    });

    return projects.flatMap((p) => {
      return p.artifacts
        .map((a) => {
          const rawURL = a.artifact.url;
          const repo = { owner: "", repo: "" };
          if (!rawURL) {
            return repo;
          }
          const repoURL = new URL(rawURL);
          if (repoURL.host !== "github.com") {
            return repo;
          }
          const splitName = repoURL.pathname.slice(1).split("/");
          if (splitName.length !== 2) {
            return repo;
          }
          return {
            owner: splitName[0],
            repo: splitName[1],
          };
        })
        .filter((r) => {
          return r.owner !== "" && r.repo !== "";
        });
    });
  }

  private async *loadAllStarHistoryForRepo(repo: {
    owner: string;
    repo: string;
  }): AsyncGenerator<Starring> {
    const iterator = unpaginateIterator<RepoFollowingSummaryResponse>()(
      REPOSITORY_FOLLOWING_SUMMARY,
      "repository.stargazers.edges",
      "repository.stargazers.pageInfo",
      {
        owner: repo.owner,
        name: repo.repo,
      },
    );
    let aggregateStatsRecorded = false;
    for await (const data of iterator) {
      const response = data.raw as RepoFollowingSummaryResponse;
      if (!aggregateStatsRecorded) {
        // Hack to make this work. we need to change how the unpaginate works
        await this.recordStarAggregateStats(repo, response);
        logger.debug("record forks");
        await this.recordForkEvents(repo, response);
        logger.debug("record watchers");
        await this.recordWatcherEvents(repo, response);
        aggregateStatsRecorded = true;
      }

      for (const star of data.results) {
        yield star as Starring;
      }
    }
  }

  private async *loadAllForksHistory(repo: {
    owner: string;
    repo: string;
  }): AsyncGenerator<Fork> {
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
      const response = data.raw as GetAllPublicForks;
      for (const star of data.results) {
        yield star.node;
      }
    }
  }

  private async recordStarAggregateStats(
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

    this.recorder.record({
      eventTime: startOfDay,
      eventType: EventType.STAR_AGGREGATE_STATS,
      artifact: artifact,
      amount: starCount,
      details: {
        starCount,
      },
    });

    return this.recorder.wait(EventType.STAR_AGGREGATE_STATS);
  }

  private async recordWatcherEvents(
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
    this.recorder.record({
      eventTime: startOfDay,
      eventType: EventType.WATCHER_AGGREGATE_STATS,
      artifact: artifact,
      amount: watchersCount,
      details: {
        watchersCount,
      },
    });

    return this.recorder.wait(EventType.WATCHER_AGGREGATE_STATS);
  }

  private async recordForkEvents(
    repo: GithubRepoLocator,
    response: RepoFollowingSummaryResponse,
  ) {
    const artifact: IncompleteArtifact = {
      name: `${repo.owner}/${repo.repo}`,
      type: ArtifactType.GIT_REPOSITORY,
      namespace: ArtifactNamespace.GITHUB,
    };
    const startOfDay = DateTime.now().startOf("day");
    const forkCount = response.repository.forkCount;

    // Get the aggregate stats for forking
    this.recorder.record({
      eventTime: startOfDay,
      eventType: EventType.FORK_AGGREGATE_STATS,
      artifact: artifact,
      amount: forkCount,
      details: {
        forkCount,
      },
    });

    const recordForkedEvent = (f: Fork) => {
      const createdAt = DateTime.fromISO(f.createdAt);
      const contributor = {
        name: f.owner.login,
        namespace:
          f.owner.__typename == "Organization"
            ? ContributorNamespace.GITHUB_ORG
            : ContributorNamespace.GITHUB_USER,
      };
      this.recorder.record({
        eventTime: createdAt,
        eventType: EventType.FORKED,
        artifact: artifact,
        contributor: contributor,
        amount: 0,
        details: {
          githubId: f.id,
        },
      });
    };

    // If we have more forks than 100 we need to make some additional queries to gather information
    if (forkCount > 100) {
      logger.debug("loading fork history");
      for await (const fork of this.loadAllForksHistory(repo)) {
        recordForkedEvent(fork);
      }
    } else {
      response.repository.forks.edges.forEach((e) => recordForkedEvent(e.node));
    }

    await this.recorder.wait(EventType.FORK_AGGREGATE_STATS);
    return this.recorder.wait(EventType.FORKED);
  }

  private async recordEventsForRepo(repo: GithubRepoLocator) {
    const artifact: IncompleteArtifact = {
      name: `${repo.owner}/${repo.repo}`,
      type: ArtifactType.GIT_REPOSITORY,
      namespace: ArtifactNamespace.GITHUB,
    };
    for await (const starring of this.loadAllStarHistoryForRepo(repo)) {
      const commitTime = DateTime.fromISO(starring.starredAt);
      const contributor =
        starring.node && starring.node.login !== ""
          ? {
              name: starring.node.login,
              namespace: ContributorNamespace.GITHUB_USER,
            }
          : undefined;

      const event: IncompleteEvent = {
        eventTime: commitTime,
        eventType: EventType.STARRED,
        artifact: artifact,
        contributor: contributor,
        amount: 0,
      };

      this.recorder.record(event);
    }

    // Wait for all of the events for this repo to be recorded
    await this.recorder.wait(EventType.STARRED);
  }
}

export type LoadRepositoryFollowers = CommonArgs & {
  skipExisting?: boolean;
};

export async function loadRepositoryFollowers(
  _args: LoadRepositoryFollowers,
): Promise<void> {
  logger.info("loading stars");

  const recorder = new BatchEventRecorder(prismaClient);
  const fetcher = new GithubFollowingFetcher(prismaClient, recorder);

  await fetcher.run();
  await recorder.waitAll();
  logger.info("done");
}
