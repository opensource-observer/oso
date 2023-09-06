import { DateTime } from "luxon";
import {
  BasicEventTypeStrategy,
  IEventRecorder,
  IncompleteArtifact,
  IncompleteContributor,
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
import { unpaginateIterator } from "../../../events/github/unpaginate.js";
import { gql } from "graphql-request";
import { GithubGraphQLResponse, GraphQLNode, Actor } from "./common.js";

type GithubRepoLocator = { owner: string; repo: string };

const GET_ISSUE_TIMELINE = gql`
  query GetIssueTimeline($id: ID!, $cursor: String) {
    node(id: $id) {
      ... on Issue {
        timelineItems(
          first: 100
          itemTypes: [REOPENED_EVENT, CLOSED_EVENT, REMOVED_FROM_PROJECT_EVENT]
          after: $cursor
        ) {
          edges {
            node {
              __typename
              ... on Node {
                id
              }
              ... on ReopenedEvent {
                createdAt
                actor {
                  login
                }
              }
              ... on ClosedEvent {
                createdAt
                actor {
                  login
                }
              }
              ... on RemovedFromProjectEvent {
                createdAt
                actor {
                  login
                }
              }
            }
          }
          pageInfo {
            hasNextPage
            endCursor
          }
        }
      }
      ... on PullRequest {
        timelineItems(
          first: 100
          itemTypes: [REOPENED_EVENT, CLOSED_EVENT, REMOVED_FROM_PROJECT_EVENT]
          after: $cursor
        ) {
          edges {
            node {
              __typename
              ... on Node {
                id
              }
              ... on ReopenedEvent {
                createdAt
                actor {
                  login
                }
              }
              ... on ClosedEvent {
                createdAt
                actor {
                  login
                }
              }
              ... on RemovedFromProjectEvent {
                createdAt
                actor {
                  login
                }
              }
            }
          }
          pageInfo {
            hasNextPage
            endCursor
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

const GET_PULL_REQUEST_REVIEWS = gql`
  query GetPullRequestReviews($id: ID!, $cursor: String) {
    node(id: $id) {
      ... on PullRequest {
        reviews(first: 100, states: [APPROVED], after: $cursor) {
          edges {
            node {
              id
              createdAt
              author {
                login
              }
            }
          }
          pageInfo {
            hasNextPage
            endCursor
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

const GET_ALL_ISSUES_AND_PRS = gql`
  query GetAllIssues($first: Int!, $searchStr: String!, $cursor: String) {
    search(first: $first, type: ISSUE, query: $searchStr, after: $cursor) {
      count: issueCount
      edges {
        node {
          __typename
          ... on Issue {
            id
            repository {
              nameWithOwner
              name
            }
            number
            title
            url
            createdAt
            updatedAt
            closedAt
            state
            author {
              login
            }

            openCloseEvents: timelineItems(
              first: 100
              itemTypes: [
                CLOSED_EVENT
                REMOVED_FROM_PROJECT_EVENT
                REOPENED_EVENT
              ]
            ) {
              edges {
                node {
                  __typename
                  ... on ReopenedEvent {
                    id
                    createdAt
                    actor {
                      login
                    }
                  }
                  ... on ClosedEvent {
                    id
                    createdAt
                    actor {
                      login
                    }
                  }
                  ... on RemovedFromProjectEvent {
                    id
                    createdAt
                    actor {
                      login
                    }
                  }
                }
              }
              pageInfo {
                hasNextPage
                endCursor
              }
            }
          }
          ... on PullRequest {
            id
            repository {
              nameWithOwner
              name
            }
            number
            title
            url
            createdAt
            updatedAt
            closedAt
            state
            author {
              login
            }
            openCloseEvents: timelineItems(
              first: 100
              itemTypes: [
                CLOSED_EVENT
                REMOVED_FROM_PROJECT_EVENT
                REOPENED_EVENT
              ]
            ) {
              edges {
                node {
                  __typename
                  ... on ReopenedEvent {
                    id
                    createdAt
                    actor {
                      login
                    }
                  }
                  ... on ClosedEvent {
                    id
                    createdAt
                    actor {
                      login
                    }
                  }
                  ... on RemovedFromProjectEvent {
                    id
                    createdAt
                    actor {
                      login
                    }
                  }
                }
              }
              pageInfo {
                hasNextPage
                endCursor
              }
            }

            mergedAt
            merged
            mergedBy {
              login
            }
            reviews(first: 100, states: [APPROVED, CHANGES_REQUESTED]) {
              edges {
                node {
                  __typename
                  id
                  createdAt
                  author {
                    login
                  }
                  state
                }
              }
              pageInfo {
                hasNextPage
                endCursor
              }
            }
            reviewCount: reviews(first: 1) {
              totalCount
            }
          }
        }
      }
      pageInfo {
        hasNextPage
        endCursor
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

// Replace this with something generated eventually.
// Too much to setup for now.
export type IssueOrPullRequest = {
  __typename: string;
  id: string;
  repository: {
    nameWithOwner: string;
    name: string;
  };
  title: string;
  url: string;
  createdAt: string;
  updatedAt: string;
  closedAt: string | null;
  state: string;
  author: Actor | null;
  mergedAt: string | null | undefined;
  merged: boolean;
  mergedBy: Actor | null;
  reviews?: Query<Review>;
  openCloseEvents: Query<IssueEvent>;
};

export type Query<T> = {
  edges: GraphQLNode<T>[];
  pageInfo: {
    hasNextPage: boolean;
    endCursor: string;
  };
};

export type IssueEvent = {
  __typename: string;
  id: string;
  createdAt: string;
  actor: Actor | null;
};

export type Review = {
  id: string;
  createdAt: string;
  state: string;
  author: Actor | null;
};

export type GetIssueTimelineResponse = GithubGraphQLResponse<{
  node: {
    timelineItems: Query<IssueEvent>;
  };
}>;

export type GetPullRequestReviewsResponse = GithubGraphQLResponse<{
  node: {
    reviews: Query<Review>;
  };
}>;

export type GetLatestUpdatedIssuesResponse = GithubGraphQLResponse<{
  search: Query<IssueOrPullRequest> & { count: number };
}>;

export class GithubPullRequestFetcher {
  private recorder: IEventRecorder;
  private prisma: PrismaClient;

  // Some of these event names are arbitrary
  private eventTypeMapping: Record<string, { [issueType: string]: EventType }> =
    {
      CreatedEvent: {
        Issue: EventType.ISSUE_CREATED,
        PullRequest: EventType.PULL_REQUEST_CREATED,
      },
      ClosedEvent: {
        Issue: EventType.ISSUE_CLOSED,
        PullRequest: EventType.PULL_REQUEST_CLOSED,
      },
      ReopenedEvent: {
        Issue: EventType.ISSUE_REOPENED,
        PullRequest: EventType.PULL_REQUEST_REOPENED,
      },
      RemovedFromProjectEvent: {
        Issue: EventType.ISSUE_REMOVED_FROM_PROJECT,
        PullRequest: EventType.PULL_REQUEST_REMOVED_FROM_PROJECT,
      },
      MergedEvent: {
        PullRequest: EventType.PULL_REQUEST_MERGED,
      },
      PullRequestApprovedEvent: {
        PullRequest: EventType.PULL_REQUEST_APPROVED,
      },
    };

  constructor(prisma: PrismaClient, recorder: IEventRecorder) {
    this.prisma = prisma;
    this.recorder = recorder;
  }

  private setupRecorder() {
    const pullRequestTypesSetup = (type: EventType) => {
      this.recorder.registerEventType(
        type,
        new BasicEventTypeStrategy(
          {
            eventType: type,
          },
          async (directory, event) => {
            const details = event.details as { githubId: string };
            const artifact = await directory.artifactFromId(event.artifactId);
            return `${artifact.name}::${artifact.namespace}::${details.githubId}`;
          },
          async (_directory, event) => {
            const details = event.details as { githubId: string };
            const artifact = event.artifact;
            return `${artifact.name}::${artifact.namespace}::${details.githubId}`;
          },
        ),
      );
    };

    pullRequestTypesSetup(EventType.PULL_REQUEST_MERGED);
    pullRequestTypesSetup(EventType.PULL_REQUEST_CREATED);
    pullRequestTypesSetup(EventType.PULL_REQUEST_CLOSED);
    pullRequestTypesSetup(EventType.PULL_REQUEST_APPROVED);
    pullRequestTypesSetup(EventType.PULL_REQUEST_REMOVED_FROM_PROJECT);
    pullRequestTypesSetup(EventType.ISSUE_CREATED);
    pullRequestTypesSetup(EventType.ISSUE_CLOSED);
    pullRequestTypesSetup(EventType.ISSUE_REOPENED);
    pullRequestTypesSetup(EventType.ISSUE_REMOVED_FROM_PROJECT);

    this.recorder.setActorScope(
      [ArtifactNamespace.GITHUB],
      [ContributorNamespace.GITHUB_USER],
    );
  }

  async run() {
    this.setupRecorder();

    const projectRepos = await this.loadRelevantRepos();

    for (const repos of projectRepos) {
      await this.recordEventsForProject(repos);
    }

    // Report that we've completed the job
    await this.recorder.waitAll();
  }

  private async loadRelevantRepos(): Promise<GithubRepoLocator[][]> {
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
      return (
        p.artifacts
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
          })
          // JANKY! We need to fix this whole section
          .reduce<GithubRepoLocator[][]>(
            (acc, curr) => {
              const batch = acc[acc.length - 1];
              if (batch.length >= 100) {
                acc.push([curr]);
              } else {
                batch.push(curr);
              }
              return acc;
            },
            [[]],
          )
      );
    });
  }

  private async *loadAllIssuesForRepos(
    repos: GithubRepoLocator[],
  ): AsyncGenerator<IssueOrPullRequest> {
    let searchStrSuffix = "";
    while (true) {
      const searchStr =
        repos.map((r) => `repo:${r.owner}/${r.repo}`).join(" ") +
        " sort:updated-desc " +
        searchStrSuffix;
      console.log(`Searching with searchStr=${searchStr}`);
      const iterator = unpaginateIterator<GetLatestUpdatedIssuesResponse>()(
        GET_ALL_ISSUES_AND_PRS,
        "search.edges",
        "search.pageInfo",
        {
          first: 100,
          searchStr: searchStr,
        },
      );

      let count = 0;
      let totalResults = 0;
      let lastUpdatedAt: string = "";

      for await (const edges of iterator) {
        const searchMeta = edges.raw as {
          search: {
            count: number;
          };
        };
        if (searchMeta.search.count) {
          totalResults = searchMeta.search.count;
        }

        for (const edge of edges.results) {
          yield edge.node;
          lastUpdatedAt = edge.node.updatedAt;
          count += 1;
        }
      }
      // Hack for now... this should go somewhere else.
      await this.recorder.waitAll();

      if (totalResults > count) {
        logger.debug(
          `looping again to limited results from github. total remaining results ${
            totalResults - count
          }`,
        );
        if (lastUpdatedAt) {
          const lastUpdatedAtDt = DateTime.fromISO(lastUpdatedAt);
          // Some overlap is expected but we will try to keep it minimal.
          searchStrSuffix = ` updated:<${lastUpdatedAtDt
            .plus({ hours: 6 })
            .toISO()} `;
        } else {
          break;
        }
      } else {
        break;
      }
    }
  }

  private async *loadIssueTimeline(id: string): AsyncGenerator<IssueEvent> {
    logger.debug(`loading issue timeline for ${id}`);
    const iterator = unpaginateIterator<GetIssueTimelineResponse>()(
      GET_ISSUE_TIMELINE,
      "node.timelineItems.edges",
      "node.timelineItems.pageInfo",
      {
        first: 100,
        id: id,
      },
    );

    for await (const edges of iterator) {
      for (const edge of edges.results) {
        yield edge.node;
      }
    }
  }

  private async *loadReviews(id: string): AsyncGenerator<Review> {
    logger.debug(`loading reviews timeline for ${id}`);
    const iterator = unpaginateIterator<GetPullRequestReviewsResponse>()(
      GET_PULL_REQUEST_REVIEWS,
      "node.reviews.edges",
      "node.reviews.pageInfo",
      {
        id: id,
      },
    );
    for await (const edges of iterator) {
      for (const edge of edges.results) {
        yield edge.node;
      }
    }
  }

  private getEventType(eventTypeStr: string, issueType: string) {
    const eventTypeMap = this.eventTypeMapping[eventTypeStr];
    if (!eventTypeMap) {
      console.log(`no map for ${eventTypeStr}`);
    }
    const eventType = this.eventTypeMapping[eventTypeStr][issueType];
    if (!eventType) {
      throw new Error(`invalid event ${eventTypeStr} type for  ${issueType}`);
    }
    return eventType;
  }

  private async recordEventsForProject(repos: GithubRepoLocator[]) {
    if (repos.length > 0) {
      console.log(`Loading events for repos ${repos[0].owner}`);
    }
    for await (const issue of this.loadAllIssuesForRepos(repos)) {
      const artifact: IncompleteArtifact = {
        name: issue.repository.nameWithOwner,
        namespace: ArtifactNamespace.GITHUB,
        type: ArtifactType.GIT_REPOSITORY,
      };
      const creationTime = DateTime.fromISO(issue.createdAt);

      // Github replaces author with null if the user has been deleted from github.
      let contributor: IncompleteContributor | undefined = undefined;
      if (issue.author !== null && issue.author !== undefined) {
        if (issue.author.login !== "") {
          contributor = {
            name: issue.author.login,
            namespace: ContributorNamespace.GITHUB_USER,
          };
        }
      }
      const githubId = issue.id;
      const eventType = this.getEventType("CreatedEvent", issue.__typename);

      const creationEvent: IncompleteEvent = {
        eventTime: creationTime,
        eventType: eventType,
        artifact: artifact,
        amount: 0,
        contributor: contributor,
        details: {
          githubId,
        },
      };

      // Record creation
      this.recorder.record(creationEvent);

      // Record merging of a pull request
      if (issue.mergedAt) {
        const mergedTime = DateTime.fromISO(issue.mergedAt);

        this.recorder.record({
          eventTime: mergedTime,
          eventType: this.getEventType("MergedEvent", issue.__typename),
          artifact: artifact,
          amount: 0,
          contributor: creationEvent.contributor,
          details: {
            githubId,
            mergedBy: issue.mergedBy!.login,
          },
        });
      }

      // Find any reviews
      await this.recordReviews(artifact, issue);

      // Find and record any close/open events
      await this.recordOpenCloseEvents(artifact, issue);
    }
    // Wait for all of the events for this owner to be recorded
    await this.recorder.waitAll();
  }

  private async recordReviews(
    artifact: IncompleteArtifact,
    issue: IssueOrPullRequest,
  ) {
    if (!issue.reviews) {
      return;
    }
    const recordReview = (review: Review) => {
      const createdAt = DateTime.fromISO(review.createdAt);
      const contributor: IncompleteContributor | undefined =
        review.author && review.author.login !== ""
          ? {
              name: review.author.login,
              namespace: ContributorNamespace.GITHUB_USER,
            }
          : undefined;

      this.recorder.record({
        eventTime: createdAt,
        eventType: this.getEventType(
          "PullRequestApprovedEvent",
          issue.__typename,
        ),
        artifact: artifact,
        amount: 0,
        contributor: contributor,
        details: {
          githubId: review.id,
        },
      });
    };

    if (issue.reviews.pageInfo.hasNextPage) {
      for await (const review of this.loadReviews(issue.id)) {
        recordReview(review);
      }
    } else {
      issue.reviews.edges.forEach((n) => recordReview(n.node));
    }
  }

  private async recordOpenCloseEvents(
    artifact: IncompleteArtifact,
    issue: IssueOrPullRequest,
  ) {
    if (!issue.openCloseEvents.edges) {
      return;
    }
    const recordOpenCloseEvent = (event: IssueEvent) => {
      const createdAt = DateTime.fromISO(event.createdAt);
      const contributor: IncompleteContributor | undefined =
        event.actor && event.actor.login !== ""
          ? {
              name: event.actor.login,
              namespace: ContributorNamespace.GITHUB_USER,
            }
          : undefined;

      this.recorder.record({
        eventTime: createdAt,
        eventType: this.getEventType(event.__typename, issue.__typename),
        artifact: artifact,
        amount: 0,
        contributor: contributor,
        details: {
          githubId: event.id,
        },
      });
    };
    if (issue.openCloseEvents.pageInfo.hasNextPage) {
      for await (const event of this.loadIssueTimeline(issue.id)) {
        recordOpenCloseEvent(event);
      }
    } else {
      issue.openCloseEvents.edges.forEach((n) => recordOpenCloseEvent(n.node));
    }
  }
}

export type LoadPullRequests = CommonArgs & {
  skipExisting?: boolean;
};

export async function loadPullRequests(_args: LoadPullRequests): Promise<void> {
  logger.info("loading pull requests");

  const recorder = new BatchEventRecorder(prismaClient);
  const fetcher = new GithubPullRequestFetcher(prismaClient, recorder);

  await fetcher.run();
  await recorder.waitAll();

  logger.info("done");
}
