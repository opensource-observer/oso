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
import { GithubGraphQLResponse, Actor } from "./common.js";
import {
  unpaginateIterator,
  PageInfo,
} from "../../../events/github/unpaginate.js";

const GET_STAR_HISTORY = gql`
  query GetStarHistory($owner: String!, $name: String!, $cursor: String) {
    repository(owner: $owner, name: $name) {
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

type GetStarHistoryResponse = GithubGraphQLResponse<{
  repository: {
    stargazers: {
      pageInfo: PageInfo;
      totalCount: number;
      edges: Starring[];
    };
  };
}>;

type GithubRepoLocator = { owner: string; repo: string };

export class GithubStarFetcher {
  private recorder: IEventRecorder;
  private prisma: PrismaClient;

  constructor(prisma: PrismaClient, recorder: IEventRecorder) {
    this.prisma = prisma;
    this.recorder = recorder;
  }

  async run() {
    this.recorder.setActorScope(
      [ArtifactNamespace.GITHUB],
      [ContributorNamespace.GITHUB_USER],
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
          in: ["0xSplits", "gnosis-safe", "Uniswap"],
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
    const iterator = unpaginateIterator<GetStarHistoryResponse>()(
      GET_STAR_HISTORY,
      "repository.stargazers.edges",
      "repository.stargazers.pageInfo",
      {
        owner: repo.owner,
        name: repo.repo,
      },
    );
    let aggregateStatsRecorded = false;
    for await (const data of iterator) {
      if (!aggregateStatsRecorded) {
        console.log(data.raw);
        // Hack to make this work. we need to change how the unpaginate works
        await this.recordStarAggregateStats(
          repo,
          data.raw as GetStarHistoryResponse,
        );
        aggregateStatsRecorded = true;
      }

      for (const star of data.results) {
        yield star as Starring;
      }
    }
  }

  private async recordStarAggregateStats(
    repo: GithubRepoLocator,
    response: GetStarHistoryResponse,
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

    this.recorder.wait(EventType.STAR_AGGREGATE_STATS);
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

export type LoadStars = CommonArgs & {
  skipExisting?: boolean;
};

export async function loadStars(_args: LoadStars): Promise<void> {
  logger.info("loading stars");

  const recorder = new BatchEventRecorder(prismaClient);
  const fetcher = new GithubStarFetcher(prismaClient, recorder);

  await fetcher.run();
  await recorder.waitAll();
  logger.info("done");
}
