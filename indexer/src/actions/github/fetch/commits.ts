import { DateTime } from "luxon";
import _ from "lodash";
import {
  IEventRecorder,
  IncompleteArtifact,
  IncompleteEvent,
  RecordHandle,
} from "../../../recorder/types.js";
import { Range, rangeToString } from "../../../utils/ranges.js";
import { gql } from "graphql-request";
import {
  Artifact,
  ArtifactNamespace,
  ArtifactType,
  Project,
} from "../../../db/orm-entities.js";
import { logger } from "../../../utils/logger.js";
import { Octokit, RequestError } from "octokit";
import { GetResponseDataTypeFromEndpointMethod } from "@octokit/types";
import { Repository } from "typeorm";
import {
  IArtifactGroup,
  IArtifactGroupCommitmentProducer,
} from "../../../scheduler/types.js";
import {
  TimeSeriesCacheLookup,
  TimeSeriesCacheWrapper,
} from "../../../cacher/time-series.js";
import { asyncBatch } from "../../../utils/array.js";
import {
  GithubBaseCollectorOptions,
  GithubBatchedProjectArtifactsBaseCollector,
  GithubGraphQLResponse,
} from "./common.js";
import { Batch } from "../../../scheduler/common.js";

const validateEmail = (email: string) => {
  return String(email)
    .toLowerCase()
    .match(
      /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|.(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/,
    );
};

const GET_COMMITS_FOR_MANY_REPOSITORIES = gql`
  query GetCommitsForManyRepositories(
    $searchStr: String!
    $first: Int
    $since: GitTimestamp
    $until: GitTimestamp
    $cursor: String
  ) {
    rateLimit {
      resetAt
      remaining
      nodeCount
      cost
    }
    search(query: $searchStr, type: REPOSITORY, first: $first, after: $cursor) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        ... on Repository {
          nameWithOwner
          isFork
          defaultBranchRef {
            name
            target {
              ... on Commit {
                history(first: $first, since: $since, until: $until) {
                  totalCount
                  nodes {
                    ... on Commit {
                      committedDate
                      authoredDate
                      oid
                      committer {
                        user {
                          login
                        }
                        name
                        email
                      }
                      author {
                        user {
                          login
                        }
                        name
                        email
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
`;

type RespositorySummariesResponse = GithubGraphQLResponse<RepositorySummaries>;

type RepositorySummaries = {
  search: {
    pageInfo: {
      hasNextPage: boolean;
      endCursor: string;
    };
    nodes: RepositorySummary[];
  };
};

type RepositorySummary = {
  nameWithOwner: string;
  isFork: boolean;
  defaultBranchRef: {
    name: string;
    target: {
      history: {
        totalCount: number;
        nodes: SummaryCommitInfo[];
      };
    };
  } | null;
};

type CommitUser = {
  login: string;
};

type GenericCommit = {
  committer: {
    login: string;
    name?: string | null | undefined;
    email?: string | null | undefined;
  } | null;
  author: {
    login: string;
    name?: string | null | undefined;
    email?: string | null | undefined;
  } | null;
};

type SummaryCommitInfo = {
  committedDate: string | undefined;
  authoredDate: string | undefined;
  oid: string;
  committer: {
    user: CommitUser | null;
    name: string;
    email: string;
  };
  author: {
    user: CommitUser | null;
    name: string;
    email: string;
  };
};

type Commit = GetResponseDataTypeFromEndpointMethod<
  Octokit["rest"]["repos"]["getCommit"]
>;

interface EmptyRepository {
  isEmptyRepository: boolean;
}

type CommitsResponse = Commit[] | EmptyRepository;

const DefaultGithubCommitCollectorOptions: GithubBaseCollectorOptions = {
  cacheOptions: {
    bucket: "github-commits",
  },
};

type RepoSummaryProcessedResult = {
  repo: Artifact;
  count: number;
  events: IncompleteEvent[];
};
type RepoSummaryProcessedResults = {
  unchanged: Artifact[];
  changed: RepoSummaryProcessedResult[];
};

export class GithubCommitCollector extends GithubBatchedProjectArtifactsBaseCollector {
  private gh: Octokit;

  constructor(
    projectRepository: Repository<Project>,
    gh: Octokit,
    recorder: IEventRecorder,
    cache: TimeSeriesCacheWrapper,
    batchSize: number,
    options?: Partial<GithubBaseCollectorOptions>,
  ) {
    const opts = _.merge(DefaultGithubCommitCollectorOptions, options);
    super(projectRepository, recorder, cache, batchSize, opts);
    this.gh = gh;
  }

  async gatherSummary(
    missingRepos: Artifact[],
    range: Range,
  ): Promise<RepoSummaryProcessedResults> {
    const results: RepoSummaryProcessedResults = {
      changed: [],
      unchanged: [],
    };

    const repoMap = missingRepos.reduce<Record<string, Artifact>>(
      (acc, curr) => {
        acc[curr.name.toLowerCase()] = curr;
        return acc;
      },
      {},
    );

    const repoSearchStr = Object.keys(repoMap).map((n) => `repo:${n}`);

    let resultCount = 0;

    const searchStr = `${repoSearchStr.join(" ")} fork:true sort:updated-desc`;

    // Do the summary search
    const pages = this.cache.loadCachedOrRetrieve<RespositorySummariesResponse>(
      TimeSeriesCacheLookup.new(
        `${this.options.cacheOptions.bucket}/summaries`,
        repoSearchStr,
        range,
      ),
      async (missing, lastPage) => {
        const response = (await this.rateLimitedGraphQLRequest(
          GET_COMMITS_FOR_MANY_REPOSITORIES,
          {
            searchStr: searchStr,
            since: missing.range.startDate.toUTC().toISO(),
            until: missing.range.endDate.toUTC().toISO(),
            first: 100,
            cursor:
              lastPage?.cursor !== undefined ? lastPage.cursor : undefined,
          },
        )) as RespositorySummariesResponse;
        const hasNextPage = response.search.pageInfo.hasNextPage;
        const cursor = response.search.pageInfo.endCursor;
        return {
          raw: response,
          cacheRange: missing.range,
          cursor: cursor,
          hasNextPage: hasNextPage,
        };
      },
    );

    for await (const page of pages) {
      const response = page.raw;
      for (const summary of response.search.nodes) {
        const repoName = summary.nameWithOwner.toLowerCase();
        const repo = repoMap[repoName];
        if (!repo) {
          // skip things are aren't monitoring (at the moment)
          continue;
        }
        delete repoMap[repoName];
        if (!summary.defaultBranchRef) {
          // This means the repository is empty (at least that's how it will be interpreted)
          summary.defaultBranchRef = {
            name: "n/a",
            target: {
              history: {
                totalCount: 0,
                nodes: [],
              },
            },
          };
        }
        const totalCount = summary.defaultBranchRef!.target.history.totalCount;
        resultCount += totalCount;
        // Ignore things that are forks
        if (totalCount === 0 || summary.isFork) {
          results.unchanged.push(repo);
        } else {
          // Create store the events for later
          results.changed.push({
            repo: repo,
            count: totalCount,
            events: this.createEventsFromSummaryResults(repo, summary),
          });
        }
      }
    }
    logger.debug(`Results in github commits summary ${resultCount}`);
    const repoMapLen = Object.keys(repoMap).length;
    if (repoMapLen !== 0) {
      logger.debug(
        `${repoMapLen} repos were missed in the summary, force retrieval`,
      );
      for (const repoName in repoMap) {
        results.changed.push({
          repo: repoMap[repoName],
          count: 1,
          events: [],
        });
      }
    }
    return results;
  }

  private createEventsFromSummaryResults(
    repo: Artifact,
    summary: RepositorySummary,
  ): IncompleteEvent[] {
    return summary
      .defaultBranchRef!.target.history.nodes.map((e) => {
        const contributor = this.contributorFromCommit({
          committer:
            e.committer.user === null
              ? null
              : {
                  email: e.committer.email,
                  name: e.committer.name,
                  login: e.committer.user.login || "",
                },
          author: {
            email: e.author.email,
            name: e.author.name,
            login: e.author.user?.login || "",
          },
        });

        // Committed date is the date it was pushed to the repo. As opposed to
        // the day it was written. This is likely more important however we'll
        // make some decisions on this later. Pragmatically this is good enough
        // and is more consistent with the `updatedAt` filtering that this
        // collector utilizes.
        let time = DateTime.fromISO(e.committedDate || "");
        if (!time.isValid) {
          time = DateTime.fromISO(e.authoredDate || "");
        }
        if (!time.isValid) {
          logger.debug("invalid date for commit. skipping");
          return undefined;
        }
        return {
          time: time,
          to: repo,
          from: contributor,
          sourceId: e.oid,
          type: {
            name: "COMMIT_CODE",
            version: 1,
          },
          amount: 1,
        };
      })
      .filter((s) => s !== undefined) as IncompleteEvent[];
  }

  async collect(
    group: IArtifactGroup<Batch>,
    range: Range,
    committer: IArtifactGroupCommitmentProducer,
  ) {
    const artifacts = await group.artifacts();

    // Check if the preprocessing has everything cached
    const summaryResults = await this.gatherSummary(artifacts, range);

    // Commit the unchanged artifacts
    for (const repo of summaryResults.unchanged) {
      committer.commit(repo).withNoChanges();
    }

    // Load commits for each artifact
    await asyncBatch(summaryResults.changed, 10, async (batch) => {
      for (const summary of batch) {
        const artifact = summary.repo;

        try {
          const handles = await asyncBatch(summary.events, 1, async (e) => {
            return this.recorder.record(e[0]);
          });
          if (summary.count !== summary.events.length) {
            handles.push(...(await this.recordEventsForRepo(artifact, range)));
          }
          committer.commit(artifact).withHandles(handles);
        } catch (err) {
          committer.commit(artifact).withResults({
            success: [],
            errors: [err],
          });
        }
      }
    });
  }

  private async recordEventsForRepo(repoArtifact: Artifact, range: Range) {
    logger.debug(
      `Recording commits for ${repoArtifact.name} in ${rangeToString(range)}`,
    );
    const locator = this.splitGithubRepoIntoLocator(repoArtifact);
    const responses = this.cache.loadCachedOrRetrieve<CommitsResponse, number>(
      TimeSeriesCacheLookup.new(
        `${this.options.cacheOptions.bucket}/${locator.owner}/${locator.repo}`,
        [`${repoArtifact.namespace}:${repoArtifact.name}`],
        range,
      ),
      async (missing, lastPage) => {
        const currentPage = (lastPage?.cursor || 1) as number;
        try {
          logger.debug("loading page from github");
          const commits = await this.gh.rest.repos.listCommits({
            ...locator,
            ...{
              since: range.startDate
                .toUTC()
                .startOf("second")
                .toISO({ suppressMilliseconds: true })!,
              until: range.endDate
                .toUTC()
                .startOf("second")
                .toISO({ suppressMilliseconds: true })!,
              per_page: 500,
              page: lastPage?.cursor || 1,
            },
          });
          let hasNextPage = false;
          if (commits.headers.link) {
            if (commits.headers.link.indexOf('rel="next"') !== -1) {
              logger.debug(`found next page after ${currentPage}`);
              hasNextPage = true;
            }
          }

          return {
            raw: commits.data as Commit[],
            cacheRange: missing.range,
            hasNextPage: hasNextPage,
            cursor: currentPage + 1,
          };
        } catch (err) {
          const reqErr = err as RequestError;

          if (reqErr.status) {
            if (reqErr.status === 404) {
              logger.debug("repo not found");
              return {
                raw: { isEmptyRepository: true },
                cacheRange: missing.range,
                hasNextPage: false,
                cursor: 1,
              };
            }
            const reqData: { message?: string } = reqErr.response?.data || {
              message: "",
            };
            const reqDataMsg = reqData.message || "";
            if (reqDataMsg.indexOf("Git Repository is empty") !== -1) {
              logger.debug("found empty repo");
              return {
                raw: { isEmptyRepository: true },
                cacheRange: missing.range,
                hasNextPage: false,
                cursor: 1,
              };
            }
          }
          throw err;
        }
      },
    );

    const recordHandles: RecordHandle[] = [];

    for await (const page of responses) {
      const commits: Commit[] = (page.raw as EmptyRepository).isEmptyRepository
        ? []
        : (page.raw as Commit[]);
      for (const commit of commits) {
        const rawCommitTime =
          commit.commit.author?.date || commit.commit.committer?.date;
        if (!rawCommitTime) {
          logger.warn(
            `encountered a commit without a date. skipping for now. repo=${locator.owner}/${locator.repo}@${commit.sha}`,
            {
              owner: locator.owner,
              repo: locator.repo,
              sha: commit.sha,
            },
          );
          continue;
        }
        const commitTime = DateTime.fromISO(rawCommitTime);
        const event: IncompleteEvent = {
          time: commitTime,
          type: {
            name: "COMMIT_CODE",
            version: 1,
          },
          to: repoArtifact,
          amount: 1,
          sourceId: commit.sha,
        };

        const contributor = this.contributorFromCommit(commit);
        if (!contributor) {
          logger.warn(
            `encountered a commit without a login, email, or a name. recording commit without a contributor. repo=${locator.owner}/${locator.repo}@${commit.sha}`,
            {
              owner: locator.owner,
              repo: locator.repo,
              sha: commit.sha,
            },
          );
        } else {
          event.from = contributor;
        }

        recordHandles.push(await this.recorder.record(event));
      }
    }

    // Wait for all of the events for this repo to be recorded
    return recordHandles;
  }

  private contributorFromCommit(
    commit: GenericCommit,
  ): IncompleteArtifact | undefined {
    const contributor: IncompleteArtifact = {
      name: "",
      namespace: ArtifactNamespace.GITHUB,
      type: ArtifactType.GITHUB_USER,
    };
    if (commit.author) {
      contributor.name = commit.author.login;
    } else if (commit.committer) {
      contributor.name = commit.committer.login;
    }

    if (!contributor.name) {
      // We will need to resort to use the email of the user if we cannot find a
      // name
      contributor.type = ArtifactType.GIT_EMAIL;
      if (commit.author?.email) {
        contributor.name = commit.author.email;
      } else if (commit.committer?.email) {
        contributor.name = commit.committer.email;
      }
      if (!validateEmail(contributor.name || "")) {
        contributor.name = `unverified:git:data:email:${contributor.name}`;
      }
      if (!contributor.name) {
        contributor.type = ArtifactType.GIT_NAME;
        // If there's still nothing we will attempt to use a name
        if (commit.author?.name) {
          contributor.name = `unverified:git:data:name:${commit.author.name}`;
        } else if (commit.committer?.name) {
          contributor.name = `unverified:git:data:name:${commit.committer.name}`;
        }
        if (!contributor.name) {
          return undefined;
        }
      }
    }

    // Lowercase the name being stored
    contributor.name = contributor.name.toLowerCase();
    return contributor;
  }
}
