import { Repository, In } from "typeorm";
import { PageInfo } from "../../../events/github/unpaginate.js";
import {
  Artifact,
  Project,
  ArtifactType,
  ArtifactNamespace,
} from "../../../db/orm-entities.js";
import {
  IArtifactGroup,
  CollectResponse,
  IArtifactGroupCommitmentProducer,
} from "../../../scheduler/types.js";
import { Range } from "../../../utils/ranges.js";
import { GenericError } from "../../../common/errors.js";
import { IEventRecorder } from "../../../recorder/types.js";
import { TimeSeriesCacheWrapper } from "../../../cacher/time-series.js";
import { RequestDocument, Variables } from "graphql-request";
import { graphQLClient } from "../../../events/github/graphQLClient.js";
import { DateTime } from "luxon";
import { logger } from "../../../utils/logger.js";
import {
  ProjectArtifactGroup,
  ProjectArtifactsCollector,
} from "../../../scheduler/common.js";

export class IncompleteRepoName extends GenericError {}
export type GithubRepoLocator = { owner: string; repo: string };

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export type GithubGraphQLResponse<T> = T & {
  rateLimit: {
    remaining: number;
    limit: number;
    cost: number;
    resetAt: string;
  };
};

export type GraphQLNode<T> = {
  node: T;
};

export type Actor = {
  login: string;
};

export type PaginatableEdges<T> = {
  edges: T[];
  pageInfo: PageInfo;
};

export interface GithubBaseCollectorOptions {
  cacheOptions: {
    bucket: string;
  };
}

export const DefaultGithubBaseCollectorOptions: GithubBaseCollectorOptions = {
  cacheOptions: {
    bucket: "github-commits",
  },
};

export type GithubGraphQLCursor = {
  searchSuffix: string;
  githubCursor?: string;
  count: number;
};

export class GithubByProjectBaseCollector extends ProjectArtifactsCollector {
  protected recorder: IEventRecorder;
  protected cache: TimeSeriesCacheWrapper;
  protected options: GithubBaseCollectorOptions;
  protected resetTime: DateTime | null;

  constructor(
    projectRepository: Repository<Project>,
    recorder: IEventRecorder,
    cache: TimeSeriesCacheWrapper,
    options: GithubBaseCollectorOptions,
  ) {
    super(projectRepository, recorder, cache, {
      type: In([ArtifactType.GIT_REPOSITORY]),
      namespace: ArtifactNamespace.GITHUB,
    });

    this.options = options;
    this.resetTime = null;
  }

  async *groupedArtifacts(): AsyncGenerator<IArtifactGroup<Project>> {
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
      yield ProjectArtifactGroup.create(project, project.artifacts);
    }
  }

  collect(
    _group: IArtifactGroup<Project>,
    _range: Range,
    _committer: IArtifactGroupCommitmentProducer,
  ): Promise<CollectResponse> {
    throw new Error("Not implemented");
  }

  protected splitGithubRepoIntoLocator(artifact: Artifact): GithubRepoLocator {
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

  protected async rateLimitedGraphQLRequest<
    R extends GithubGraphQLResponse<object>,
  >(query: RequestDocument, variables: Variables) {
    if (this.resetTime) {
      const now = DateTime.now();
      const diffMs = this.resetTime.toMillis() - now.toMillis();
      if (diffMs > 0) {
        if (diffMs > 200) {
          logger.debug(
            `encountered rate limit on github. waiting for ${diffMs}ms`,
          );
        }
        await sleep(diffMs);
      }
    }

    const response = await graphQLClient.request<R>(query, variables);
    const rateLimit = response.rateLimit;

    if (rateLimit.remaining == 0 || rateLimit.remaining - rateLimit.cost <= 0) {
      this.resetTime = DateTime.fromISO(rateLimit.resetAt);
    } else {
      // Artificially rate limit to 5reqs/second
      this.resetTime = DateTime.now().plus(200);
    }
    return response;
  }
}
