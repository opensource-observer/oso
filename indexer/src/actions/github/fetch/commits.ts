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
  Prisma,
  PrismaClient,
} from "@prisma/client";
import { BatchEventRecorder } from "../../../recorder/recorder.js";
import { prisma as prismaClient } from "../../../db/prisma-client.js";
import { logger } from "../../../utils/logger.js";
import { CommonArgs } from "../../../utils/api.js";
import { GITHUB_TOKEN } from "../../../config.js";
import { Octokit } from "octokit";
import { GetResponseDataTypeFromEndpointMethod } from "@octokit/types";

type Commit = GetResponseDataTypeFromEndpointMethod<
  Octokit["rest"]["repos"]["getCommit"]
>;
type GithubRepoLocator = { owner: string; repo: string };

export class GithubCommitFetcher {
  private recorder: IEventRecorder;
  private gh: Octokit;
  private prisma: PrismaClient;

  constructor(prisma: PrismaClient, gh: Octokit, recorder: IEventRecorder) {
    this.prisma = prisma;
    this.recorder = recorder;
    this.gh = gh;
  }

  async run() {
    this.recorder.registerEventType(
      EventType.COMMIT_CODE,
      new BasicEventTypeStrategy(
        {
          eventType: EventType.COMMIT_CODE,
        },
        async (directory, event) => {
          const details = event.details as { sha: string };
          const artifact = await directory.artifactFromId(event.artifactId);
          return `${artifact.name}::${artifact.namespace}::${details.sha}`;
        },
        async (_directory, event) => {
          const details = event.details as { sha: string };
          const artifact = event.artifact;
          return `${artifact.name}::${artifact.namespace}::${details.sha}`;
        },
      ),
    );

    this.recorder.setActorScope(
      [ArtifactNamespace.GITHUB],
      [
        ContributorNamespace.GITHUB_USER,
        ContributorNamespace.GIT_EMAIL,
        ContributorNamespace.GIT_NAME,
      ],
    );

    const repos = await this.loadRelevantRepos();

    for (const repo of repos) {
      this.recordEventsForRepo(repo);
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

  private async *loadAllCommitsForRepo(repo: {
    owner: string;
    repo: string;
  }): AsyncGenerator<Commit> {
    const iterator = this.gh.paginate.iterator(this.gh.rest.repos.listCommits, {
      ...repo,
      ...{ per_page: 500 },
    });

    for await (const { data: commits } of iterator) {
      for (const commit of commits) {
        yield commit;
      }
    }
  }

  private async recordEventsForRepo(repo: GithubRepoLocator) {
    const artifact: IncompleteArtifact = {
      name: `${repo.owner}/${repo.repo}`,
      type: ArtifactType.GIT_REPOSITORY,
      namespace: ArtifactNamespace.GITHUB,
    };
    for await (const commit of this.loadAllCommitsForRepo(repo)) {
      const rawCommitTime =
        commit.commit.committer?.date || commit.commit.author?.date;
      if (!rawCommitTime) {
        logger.warn(
          `encountered a commit without a date. skipping for now. repo=${repo.owner}/${repo.repo}@${commit.sha}`,
          {
            owner: repo.owner,
            repo: repo.repo,
            sha: commit.sha,
          },
        );
        continue;
      }
      const commitTime = DateTime.fromISO(rawCommitTime);
      const event: IncompleteEvent = {
        eventTime: commitTime,
        eventType: EventType.COMMIT_CODE,
        artifact: artifact,
        amount: 0,
        details: {
          sha: commit.sha,
        },
      };

      const contributor = this.contributorFromCommit(commit);
      if (!contributor) {
        logger.warn(
          `encountered a commit without a login, email, or a name. recording commit without a contributor. repo=${repo.owner}/${repo.repo}@${commit.sha}`,
          {
            owner: repo.owner,
            repo: repo.repo,
            sha: commit.sha,
          },
        );
      } else {
        event.contributor = contributor;
      }

      this.recorder.record(event);
    }

    // Wait for all of the events for this repo to be recorded
    await this.recorder.wait(EventType.COMMIT_CODE);
  }

  private contributorFromCommit(
    commit: Commit,
  ): IncompleteContributor | undefined {
    const contributor: IncompleteContributor = {
      name: "",
      namespace: ContributorNamespace.GITHUB_USER,
    };
    if (commit.committer) {
      contributor.name = commit.committer.login;
    } else if (commit.author) {
      contributor.name = commit.author.login;
    }

    if (!contributor.name) {
      // We will need to resort to use the email of the user if we cannot find a
      // name
      contributor.namespace = ContributorNamespace.GIT_EMAIL;
      if (commit.commit.committer?.email) {
        contributor.name = commit.commit.committer.email;
      } else if (commit.commit.author?.email) {
        contributor.name = commit.commit.author.email;
      }
      if (!contributor.name) {
        contributor.namespace = ContributorNamespace.GIT_NAME;
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

export type LoadCommits = CommonArgs & {
  skipExisting?: boolean;
};

export async function loadCommits(args: LoadCommits): Promise<void> {
  logger.info("loading commits");

  const octokit = new Octokit({ auth: GITHUB_TOKEN });
  const recorder = new BatchEventRecorder(prismaClient);
  const fetcher = new GithubCommitFetcher(prismaClient, octokit, recorder);

  await fetcher.run();
  logger.info("done");
}
