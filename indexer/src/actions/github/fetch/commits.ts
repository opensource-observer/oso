import { DateTime } from "luxon";
import _ from "lodash";
import {
  IEventRecorder,
  IncompleteArtifact,
  IncompleteEvent,
} from "../../../recorder/types.js";
import { Range, rangeToString } from "../../../utils/ranges.js";
import {
  Artifact,
  ArtifactNamespace,
  ArtifactType,
  EventType,
  Project,
} from "../../../db/orm-entities.js";
import { logger } from "../../../utils/logger.js";
import { Octokit, RequestError } from "octokit";
import { GetResponseDataTypeFromEndpointMethod } from "@octokit/types";
import { Repository } from "typeorm";
import { IArtifactGroup } from "../../../scheduler/types.js";
import {
  TimeSeriesCacheLookup,
  TimeSeriesCacheWrapper,
} from "../../../cacher/time-series.js";
import { asyncBatch } from "../../../utils/array.js";
import { GenericError } from "../../../common/errors.js";
import {
  GithubBaseCollectorOptions,
  GithubByProjectBaseCollector,
} from "./common.js";

type Commit = GetResponseDataTypeFromEndpointMethod<
  Octokit["rest"]["repos"]["getCommit"]
>;

interface EmptyRepository {
  isEmptyRepository: boolean;
}

type CommitsResponse = Commit[] | EmptyRepository;

class IncompleteRepoName extends GenericError {}

const DefaultGithubCommitCollectorOptions: GithubBaseCollectorOptions = {
  cacheOptions: {
    bucket: "github-commits",
  },
};

export class GithubCommitCollector extends GithubByProjectBaseCollector {
  private gh: Octokit;

  constructor(
    projectRepository: Repository<Project>,
    gh: Octokit,
    recorder: IEventRecorder,
    cache: TimeSeriesCacheWrapper,
    options?: Partial<GithubBaseCollectorOptions>,
  ) {
    const opts = _.merge(DefaultGithubCommitCollectorOptions, options);
    super(projectRepository, recorder, cache, opts);
    this.gh = gh;
  }

  async collect(
    group: IArtifactGroup<Project>,
    range: Range,
    commitArtifact: (artifact: Artifact | Artifact[]) => Promise<void>,
  ) {
    const artifacts = await group.artifacts();
    const errors: unknown[] = [];

    // Load commits for each artifact
    await asyncBatch(artifacts, 10, async (batch) => {
      const artifactCommits: Promise<void>[] = [];
      for (const artifact of batch) {
        try {
          await this.recordEventsForRepo(artifact, range);
        } catch (err) {
          if (err instanceof IncompleteRepoName) {
            logger.warn(
              `artifact[${artifact.id}] has a malformed github url ${artifact.url}`,
            );
            return;
          }
          errors.push(err);
        }
        artifactCommits.push(commitArtifact(artifact));
      }
      await Promise.all(artifactCommits);
    });

    return {
      errors: errors,
    };
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
            if (reqErr.response?.data === "Git Repository is empty") {
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

    const recordPromises: Promise<string>[] = [];

    for await (const page of responses) {
      const commits: Commit[] = (page.raw as EmptyRepository).isEmptyRepository
        ? []
        : (page.raw as Commit[]);
      for (const commit of commits) {
        const rawCommitTime =
          commit.commit.committer?.date || commit.commit.author?.date;
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
          type: EventType.COMMIT_CODE,
          to: repoArtifact,
          amount: 0,
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

        recordPromises.push(this.recorder.record(event));
      }
    }

    // Wait for all of the events for this repo to be recorded
    await Promise.all(recordPromises);
  }

  private contributorFromCommit(
    commit: Commit,
  ): IncompleteArtifact | undefined {
    const contributor: IncompleteArtifact = {
      name: "",
      namespace: ArtifactNamespace.GITHUB,
      type: ArtifactType.GITHUB_USER,
    };
    if (commit.committer) {
      contributor.name = commit.committer.login;
    } else if (commit.author) {
      contributor.name = commit.author.login;
    }

    if (!contributor.name) {
      // We will need to resort to use the email of the user if we cannot find a
      // name
      contributor.type = ArtifactType.GIT_EMAIL;
      if (commit.commit.committer?.email) {
        contributor.name = commit.commit.committer.email;
      } else if (commit.commit.author?.email) {
        contributor.name = commit.commit.author.email;
      }
      if (!contributor.name) {
        contributor.type = ArtifactType.GIT_NAME;
        // If there's still nothing we will attempt to use a name
        if (commit.commit.committer?.name) {
          contributor.name = commit.commit.committer.name;
        } else if (commit.commit.author?.name) {
          contributor.name = commit.commit.author.name;
        }
        if (!contributor.name) {
          return undefined;
        }
      }
    }
    return contributor;
  }
}
