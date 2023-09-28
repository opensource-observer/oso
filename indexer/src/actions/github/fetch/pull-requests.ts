import { DateTime } from "luxon";
import {
  IEventRecorder,
  IncompleteArtifact,
  IncompleteEvent,
} from "../../../recorder/types.js";
import {
  Artifact,
  ArtifactNamespace,
  ArtifactType,
  EventType,
  Project,
} from "../../../db/orm-entities.js";
import { logger } from "../../../utils/logger.js";
import _ from "lodash";
import { unpaginateIterator } from "../../../events/github/unpaginate.js";
import { gql } from "graphql-request";
import {
  GithubGraphQLResponse,
  GraphQLNode,
  Actor,
  GithubByProjectBaseCollector,
  GithubBaseCollectorOptions,
  GithubGraphQLCursor,
} from "./common.js";
import { Repository } from "typeorm";
import {
  TimeSeriesCacheLookup,
  TimeSeriesCacheWrapper,
} from "../../../cacher/time-series.js";
import { ArtifactGroup } from "../../../scheduler/types.js";
import { Range } from "../../../utils/ranges.js";
import { graphQLClient } from "../../../events/github/graphQLClient.js";
import { asyncBatch } from "../../../utils/array.js";

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

const DefaultGithubIssueCollectorOptions: GithubBaseCollectorOptions = {
  cacheOptions: {
    bucket: "github-issues",
  },
};

export class GithubIssueCollector extends GithubByProjectBaseCollector {
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

  constructor(
    projectRepository: Repository<Project>,
    recorder: IEventRecorder,
    cache: TimeSeriesCacheWrapper,
    options?: Partial<GithubBaseCollectorOptions>,
  ) {
    const opts = _.merge(DefaultGithubIssueCollectorOptions, options);
    super(projectRepository, recorder, cache, opts);
  }

  // async run() {
  //   this.setupRecorder();

  //   const projectRepos = await this.loadRelevantRepos();

  //   for (const repos of projectRepos) {
  //     await this.recordEventsForProject(repos);
  //   }

  //   // Report that we've completed the job
  //   await this.recorder.waitAll();
  // }

  async collect(
    group: ArtifactGroup,
    range: Range,
    commitArtifact: (artifact: Artifact) => Promise<void>,
  ): Promise<void> {
    const project = group.details as Project;
    logger.debug(`collecting issues for repos of Project[${project.slug}]`);

    const locators = group.artifacts.map((a) => {
      return this.splitGithubRepoIntoLocator(a);
    });

    const pages = this.cache.loadCachedOrRetrieve<
      GraphQLNode<IssueOrPullRequest>[],
      GithubGraphQLCursor
    >(
      TimeSeriesCacheLookup.new(
        `${this.options.cacheOptions.bucket}/${project.slug}`,
        locators.map((l) => `${l.owner}/${l.repo}`),
        range,
      ),
      async (missing, lastPage) => {
        const searchStrSuffix = lastPage?.cursor?.searchSuffix || "";
        const searchStr =
          missing.keys.join(" ") + " sort:updated-desc " + searchStrSuffix;

        const cursor = lastPage?.cursor?.githubCursor;

        // Get current page of results
        const response =
          await this.rateLimitedGraphQLRequest<GetLatestUpdatedIssuesResponse>(
            GET_ALL_ISSUES_AND_PRS,
            {
              first: 100,
              searchStr: searchStr,
              cursor: cursor,
            },
          );

        let nextCursor: string | undefined = response.search.pageInfo.endCursor;
        let nextSearchSuffix = searchStrSuffix;
        let hasNextPage = response.search.pageInfo.hasNextPage;

        let count =
          (lastPage?.cursor?.count || 0) + response.search.edges.length;
        const totalResults = response.search.count;

        // If we've reaached the end of the available pages and the totalResults
        // is still greater than the number of results we've processed we need to
        // keep going. This is a bit janky
        if (!hasNextPage && totalResults > count) {
          count = 0;
          const last = response.search.edges.slice(-1)[0];
          const lastUpdatedAtDt = DateTime.fromISO(last.node.updatedAt);
          // Some overlap is expected but we will try to keep it minimal.
          nextSearchSuffix = ` updated:<${lastUpdatedAtDt
            .plus({ hours: 6 })
            .toISO()} `;
          nextCursor = undefined;
          hasNextPage = true;
        }

        return {
          raw: response.search.edges,
          hasNextPage: hasNextPage,
          cursor: {
            searchSuffix: nextSearchSuffix,
            githubCursor: nextCursor,
            count: count,
          },
          cacheRange: missing.range,
        };
      },
    );

    for await (const page of pages) {
      const edges = page.raw;
      for (const edge of edges) {
        const issue = edge.node;
        const artifact: IncompleteArtifact = {
          name: issue.repository.nameWithOwner,
          namespace: ArtifactNamespace.GITHUB,
          type: ArtifactType.GIT_REPOSITORY,
        };
        const creationTime = DateTime.fromISO(issue.createdAt);

        // Github replaces author with null if the user has been deleted from github.
        let contributor: IncompleteArtifact | undefined = undefined;
        if (issue.author !== null && issue.author !== undefined) {
          if (issue.author.login !== "") {
            contributor = {
              name: issue.author.login,
              namespace: ArtifactNamespace.GITHUB,
              type: ArtifactType.GITHUB_USER,
            };
          }
        }
        const githubId = issue.id;
        const eventType = this.getEventType("CreatedEvent", issue.__typename);

        const creationEvent: IncompleteEvent = {
          time: creationTime,
          type: eventType,
          to: artifact,
          amount: 0,
          from: contributor,
          sourceId: githubId,
        };

        // Record creation
        this.recorder.record(creationEvent);

        // Record merging of a pull request
        if (issue.mergedAt) {
          const mergedTime = DateTime.fromISO(issue.mergedAt);

          const mergedBy = issue.mergedBy !== null ? issue.mergedBy.login : "";

          this.recorder.record({
            time: mergedTime,
            type: this.getEventType("MergedEvent", issue.__typename),
            to: artifact,
            amount: 0,
            from: creationEvent.from,
            sourceId: githubId,
            details: {
              mergedBy: mergedBy,
            },
          });
        }

        // Find any reviews
        await this.recordReviews(artifact, issue);

        // Find and record any close/open events
        await this.recordOpenCloseEvents(artifact, issue);
      }
      await this.recorder.waitAll();
    }
    logger.debug(
      `completed issue collection for repos of Project[${project.slug}]`,
    );
    // Commit all artifacts for this project
    await asyncBatch(group.artifacts, 1, async (batch) => {
      return await commitArtifact(batch[0]);
    });
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

  // private async recordEventsForProject(repos: GithubRepoLocator[]) {
  //   if (repos.length > 0) {
  //     console.log(`Loading events for repos ${repos[0].owner}`);
  //   }
  //   for await (const issue of this.loadAllIssuesForRepos(repos)) {

  //   }
  //   // Wait for all of the events for this owner to be recorded
  //   await this.recorder.waitAll();
  // }

  private async recordReviews(
    artifact: IncompleteArtifact,
    issue: IssueOrPullRequest,
  ) {
    if (!issue.reviews) {
      return;
    }
    const recordReview = (review: Review) => {
      const createdAt = DateTime.fromISO(review.createdAt);
      const contributor: IncompleteArtifact | undefined =
        review.author && review.author.login !== ""
          ? {
              name: review.author.login,
              namespace: ArtifactNamespace.GITHUB,
              type: ArtifactType.GITHUB_USER,
            }
          : undefined;

      this.recorder.record({
        time: createdAt,
        type: this.getEventType("PullRequestApprovedEvent", issue.__typename),
        to: artifact,
        amount: 0,
        from: contributor,
        sourceId: review.id,
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
      const contributor: IncompleteArtifact | undefined =
        event.actor && event.actor.login !== ""
          ? {
              name: event.actor.login,
              namespace: ArtifactNamespace.GITHUB,
              type: ArtifactType.GITHUB_USER,
            }
          : undefined;

      this.recorder.record({
        time: createdAt,
        type: this.getEventType(event.__typename, issue.__typename),
        to: artifact,
        amount: 0,
        from: contributor,
        sourceId: event.id,
        details: {
          // Grab the original author's login if it's there
          originalAuthorLogin: issue.author?.login || undefined,
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

// export type LoadPullRequests = CommonArgs & {
//   skipExisting?: boolean;
// };

// export async function loadPullRequests(_args: LoadPullRequests): Promise<void> {
//   logger.info("loading pull requests");

//   const recorder = new BatchEventRecorder(prismaClient);
//   const fetcher = new GithubPullRequestCollector(prismaClient, recorder);

//   await fetcher.run();
//   await recorder.waitAll();

//   logger.info("done");
// }
