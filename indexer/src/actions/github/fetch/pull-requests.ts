import { DateTime } from "luxon";
import {
  IEventGroupRecorder,
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
  GithubRepoLocator,
} from "./common.js";
import { Repository } from "typeorm";
import {
  TimeSeriesCacheLookup,
  TimeSeriesCacheWrapper,
} from "../../../cacher/time-series.js";
import {
  IArtifactGroup,
  IArtifactGroupCommitmentProducer,
} from "../../../scheduler/types.js";
import { Range } from "../../../utils/ranges.js";
import { ArtifactGroupRecorder } from "../../../recorder/group.js";

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

  async collect(
    group: IArtifactGroup<Project>,
    range: Range,
    committer: IArtifactGroupCommitmentProducer,
  ) {
    const project = await group.meta();
    const artifacts = await group.artifacts();

    const groupRecorder = new ArtifactGroupRecorder(this.recorder);
    try {
      await this.collectEventsForRepos(
        groupRecorder,
        project,
        artifacts,
        range,
        committer,
      );
      committer.commitGroup(groupRecorder);
    } catch (err) {
      committer.failAll(err);
    }

    logger.debug(
      `completed issue collection for repos of Project[${project.slug}]`,
    );
  }

  private async collectEventsForRepos(
    groupRecorder: IEventGroupRecorder<Artifact>,
    project: Project,
    artifacts: Artifact[],
    range: Range,
    committer: IArtifactGroupCommitmentProducer,
  ) {
    const locators = artifacts
      .map((a) => {
        try {
          return this.splitGithubRepoIntoLocator(a);
        } catch (err) {
          // Errored for the current artifact. End now.
          committer.commit(a).withResults({
            errors: [err],
            success: [],
          });
          return undefined;
        }
      })
      .filter((a): a is GithubRepoLocator => {
        return a !== undefined;
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
        logger.debug("loading more from github");
        const searchStrSuffix = lastPage?.cursor?.searchSuffix || "";
        const searchStr =
          missing.keys.map((a) => `repo:${a}`).join(" ") +
          " sort:updated-desc " +
          searchStrSuffix;

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

    const errors: unknown[] = [];

    for await (const page of pages) {
      const edges = page.raw;
      for (const edge of edges) {
        // Stop processing if we've reached the end
        if (DateTime.fromISO(edge.node.updatedAt) < range.startDate) {
          return;
        }
        try {
          await this.collectEventsForIssue(
            groupRecorder,
            range,
            artifacts,
            edge.node,
          );
        } catch (err) {
          errors.push(err);
        }
      }
    }
  }

  private async collectEventsForIssue(
    groupRecorder: IEventGroupRecorder<Artifact>,
    range: Range,
    artifacts: Artifact[],
    issue: IssueOrPullRequest,
  ) {
    const artifactMap = _.keyBy(artifacts, (a: Artifact) => {
      return a.name.toLowerCase();
    });

    const repoLocatorStr = issue.repository.nameWithOwner.toLowerCase();

    const artifact = artifactMap[repoLocatorStr];
    if (!artifact) {
      // Try parsing the URL
      throw new Error(
        `unexpected repository ${issue.repository.nameWithOwner}`,
      );
    }
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
      amount: 1,
      from: contributor,
      sourceId: githubId,
    };

    // Record creation
    await groupRecorder.record(creationEvent);

    // Record merging of a pull request
    if (issue.mergedAt) {
      const mergedTime = DateTime.fromISO(issue.mergedAt);

      const mergedBy = issue.mergedBy !== null ? issue.mergedBy.login : "";

      await groupRecorder.record({
        time: mergedTime,
        type: this.getEventType("MergedEvent", issue.__typename),
        to: artifact,
        amount: 1,
        from: creationEvent.from,
        sourceId: githubId,
        details: {
          mergedBy: mergedBy,
        },
      });
    }

    // Find any reviews
    await this.recordReviews(groupRecorder, range, artifact, issue);

    // Find and record any close/open events
    await this.recordOpenCloseEvents(groupRecorder, range, artifact, issue);
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
      logger.debug(`no map for ${eventTypeStr}`);
    }
    const eventType = this.eventTypeMapping[eventTypeStr][issueType];
    if (!eventType) {
      throw new Error(`invalid event ${eventTypeStr} type for  ${issueType}`);
    }
    return eventType;
  }

  private async recordReviews(
    groupRecorder: IEventGroupRecorder<Artifact>,
    range: Range,
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

      return groupRecorder.record({
        time: createdAt,
        type: this.getEventType("PullRequestApprovedEvent", issue.__typename),
        to: artifact,
        amount: 1,
        from: contributor,
        sourceId: review.id,
      });
    };

    if (issue.reviews.pageInfo.hasNextPage) {
      logger.debug("need to load more reviews");
      for await (const review of this.loadReviews(issue.id)) {
        if (DateTime.fromISO(review.createdAt) < range.startDate) {
          break;
        }
        await recordReview(review);
      }
    } else {
      for (const edge of issue.reviews.edges) {
        if (DateTime.fromISO(edge.node.createdAt) < range.startDate) {
          break;
        }
        await recordReview(edge.node);
      }
    }
  }

  private async recordOpenCloseEvents(
    groupRecorder: IEventGroupRecorder<Artifact>,
    range: Range,
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

      return groupRecorder.record({
        time: createdAt,
        type: this.getEventType(event.__typename, issue.__typename),
        to: artifact,
        amount: 1,
        from: contributor,
        sourceId: event.id,
        details: {
          // Grab the original author's login if it's there
          originalAuthorLogin: issue.author?.login || undefined,
        },
      });
    };

    if (issue.openCloseEvents.pageInfo.hasNextPage) {
      logger.debug("need to load more open/close events");
      for await (const event of this.loadIssueTimeline(issue.id)) {
        if (DateTime.fromISO(event.createdAt) < range.startDate) {
          break;
        }
        await recordOpenCloseEvent(event);
      }
    } else {
      for (const edge of issue.openCloseEvents.edges) {
        if (DateTime.fromISO(edge.node.createdAt) < range.startDate) {
          break;
        }
        await recordOpenCloseEvent(edge.node);
      }
    }
  }
}
