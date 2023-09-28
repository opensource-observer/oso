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
import { Octokit } from "octokit";
import { GetResponseDataTypeFromEndpointMethod } from "@octokit/types";
import { In, Repository } from "typeorm";
import { ArtifactGroup, ICollector } from "../../../scheduler/types.js";
import {
  TimeSeriesCacheLookup,
  TimeSeriesCacheWrapper,
} from "../../../cacher/time-series.js";
import { asyncBatch } from "../../../utils/array.js";
import { GenericError } from "../../../common/errors.js";

type Commit = GetResponseDataTypeFromEndpointMethod<
  Octokit["rest"]["repos"]["getCommit"]
>;
type GithubRepoLocator = { owner: string; repo: string };

class IncompleteRepoName extends GenericError {}

export interface GithubCommitCollectorOptions {
  cacheOptions: {
    bucket: string;
  };
}

export const DefaultGithubCommitCollectorOptions: GithubCommitCollectorOptions =
  {
    cacheOptions: {
      bucket: "github-commits",
    },
  };

export class GithubCommitCollector implements ICollector {
  private recorder: IEventRecorder;
  private gh: Octokit;
  private projectRepository: Repository<Project>;
  private cache: TimeSeriesCacheWrapper;
  private options: GithubCommitCollectorOptions;

  constructor(
    projectRepository: Repository<Project>,
    gh: Octokit,
    recorder: IEventRecorder,
    cache: TimeSeriesCacheWrapper,
    options?: Partial<GithubCommitCollectorOptions>,
  ) {
    this.projectRepository = projectRepository;
    this.recorder = recorder;
    this.gh = gh;
    this.cache = cache;
    this.options = _.merge(DefaultGithubCommitCollectorOptions, options);
  }

  async *groupedArtifacts(): AsyncGenerator<ArtifactGroup> {
    const projects = await this.projectRepository.find({
      relations: {
        artifacts: true,
      },
      where: {
        artifacts: {
          type: In([ArtifactType.GIT_REPOSITORY]),
          namespace: ArtifactNamespace.GITHUB,
        },
      },
    });
    // Emit each project's artifacts as a group of artifacts to record
    for (const project of projects) {
      yield {
        artifacts: project.artifacts,
        details: project,
      };
    }
  }

  async collect(
    group: ArtifactGroup,
    range: Range,
    commitArtifact: (artifact: Artifact) => Promise<void>,
  ) {
    const project = group.details as Project;
    logger.debug(
      `loading all commits for repos within the Project[${project.slug}]`,
    );

    // Load commits for each artifact
    asyncBatch(group.artifacts, 1, async (batch) => {
      const artifact = batch[0];
      try {
        await this.recordEventsForRepo(artifact, range);
      } catch (err) {
        if (err instanceof IncompleteRepoName) {
          logger.warn(
            `artifact[${artifact.id}] has a malformed github url ${artifact.url}`,
          );
          return;
        }
      }
      return commitArtifact(artifact);
    });
  }

  private splitGithubRepoIntoLocator(artifact: Artifact): GithubRepoLocator {
    const rawURL = artifact.url;
    if (!rawURL) {
      throw new IncompleteRepoName(`no url for artifact[${artifact.id}]`);
    }
    const repoURL = new URL(rawURL);
    if (repoURL.host !== "github.com") {
      throw new IncompleteRepoName(`unexpected url ${rawURL}`);
    }
    const splitName = repoURL.pathname.slice(1).split("/");
    if (splitName.length !== 2) {
      throw new IncompleteRepoName(`unexpected url ${rawURL}`);
    }
    return {
      owner: splitName[0],
      repo: splitName[1],
    };
  }

  private async recordEventsForRepo(repoArtifact: Artifact, range: Range) {
    logger.debug(
      `Recording commits for ${repoArtifact.name} in ${rangeToString(range)}`,
    );
    const locator = this.splitGithubRepoIntoLocator(repoArtifact);
    const responses = this.cache.loadCachedOrRetrieve<Commit[]>(
      TimeSeriesCacheLookup.new(
        `${this.options.cacheOptions.bucket}/${locator.owner}/${locator.repo}`,
        [`${repoArtifact.namespace}:${repoArtifact.name}`],
        range,
      ),
      async (missing, lastPage) => {
        const currentPage = (lastPage?.cursor || 1) as number;
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
            page: (lastPage?.cursor || 1) as number,
          },
        });
        let hasNextPage = false;
        if (commits.headers.link) {
          hasNextPage = true;
        }

        return {
          raw: commits.data as Commit[],
          cacheRange: missing.range,
          hasNextPage: hasNextPage,
          cursor: currentPage + 1,
        };
      },
    );

    for await (const page of responses) {
      for (const commit of page.raw) {
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

        this.recorder.record(event);
      }
    }

    // Wait for all of the events for this repo to be recorded
    await this.recorder.wait(EventType.COMMIT_CODE);
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
