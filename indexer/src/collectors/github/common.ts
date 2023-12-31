import { Repository, In } from "typeorm";
import { PageInfo } from "./unpaginate.js";
import {
  Artifact,
  Project,
  ArtifactType,
  ArtifactNamespace,
} from "../../db/orm-entities.js";
import { GenericError } from "../../common/errors.js";
import { IEventRecorderClient } from "../../recorder/types.js";
import { TimeSeriesCacheWrapper } from "../../cacher/time-series.js";
import { ClientError, RequestDocument, Variables } from "graphql-request";
import { graphQLClient } from "./graphql-client.js";
import { DateTime } from "luxon";
import { logger } from "../../utils/logger.js";
import {
  BatchedProjectArtifactsCollector,
  ProjectArtifactsCollector,
} from "../../scheduler/common.js";
import { Mutex } from "async-mutex";
import {
  MultiplexGithubGraphQLRequester,
  MultiplexRequestResponse,
} from "./multiplex-graphql.js";
import { asyncBatchFlattened } from "../../utils/array.js";

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

// Create a github mixin
type Constructor = new (...args: any[]) => object;

export function GithubCollectorMixins<TBase extends Constructor>(Base: TBase) {
  return class extends Base {
    _requestMutex: Mutex;
    _resetTime: DateTime;

    constructor(...args: any[]) {
      super(...args);
      this._requestMutex = new Mutex();
      this._resetTime = DateTime.fromISO("1970-01-01T00:00:00Z");
    }

    splitGithubRepoIntoLocator(artifact: Artifact): GithubRepoLocator {
      const rawURL = artifact.url;
      if (!rawURL) {
        throw new IncompleteRepoName(`no url for artifact[${artifact.id}]`);
      }
      // Parse without any trailing slashes
      const repoURL = new URL(rawURL.replace(/\/+$/, ""));
      if (repoURL.host !== "github.com") {
        throw new IncompleteRepoName(`unexpected url ${rawURL}`);
      }
      const splitName = repoURL.pathname.slice(1).split("/");
      if (splitName.length !== 2) {
        throw new IncompleteRepoName(`unexpected url ${rawURL}`);
      }
      return {
        owner: splitName[0].toLowerCase(),
        repo: splitName[1].toLowerCase(),
      };
    }

    debugLogAnError(message: string, err: unknown) {
      logger.debug(message);
      try {
        logger.debug(JSON.stringify(err));
      } catch (_e) {
        logger.debug("could not json stringify the error");
        logger.debug(err);
      }
    }

    async rateLimitedGraphQLRequest<R extends GithubGraphQLResponse<object>>(
      query: RequestDocument,
      variables: Variables,
      allowErrors: boolean = false,
      retries: number = 10,
    ): Promise<R> {
      for (let i = 0; i < retries; i++) {
        if (this._resetTime) {
          const now = DateTime.now();
          const diffMs = this._resetTime.toMillis() - now.toMillis();
          if (diffMs > 0) {
            if (diffMs > 200) {
              logger.debug(
                `encountered rate limit on github. waiting for ${diffMs}ms`,
              );
            }
            await sleep(diffMs);
          }
        }

        const release = await this._requestMutex.acquire();
        // Hacky retry loop for 5XX errors
        try {
          const response = await graphQLClient.request<R>(query, variables, {
            Accept: "application/vnd.github.hawkgirl-preview+json",
          });
          const rateLimit = response.rateLimit;
          if (
            rateLimit.remaining == 0 ||
            rateLimit.remaining - rateLimit.cost <= 0
          ) {
            this._resetTime = DateTime.fromISO(rateLimit.resetAt);
          } else {
            // Artificially rate limit to 5reqs/second
            this._resetTime = DateTime.now().plus(100);
          }
          release();
          return response;
        } catch (err) {
          release();
          if (err instanceof ClientError) {
            // Retry up
            if (err.response.status >= 500 && err.response.status < 600) {
              logger.error("hit a github 500 error. waiting for some period");
              this.debugLogAnError("github 500 error:", err);
              this._resetTime = DateTime.now().plus({
                milliseconds: 2500 * (i + 1),
              });
              continue;
            }

            if (err.response.status === 403) {
              logger.error("likely hit a secondary rate limit. pausing 5 mins");
              this.debugLogAnError("github 403 error:", err);
              logger.debug(JSON.stringify(err));
              this._resetTime = DateTime.now().plus({ milliseconds: 300000 });
              continue;
            }
            if (err.response.status === 200) {
              if (allowErrors) {
                return err.response.data as GithubGraphQLResponse<R>;
              }
              logger.debug("very interesting! we only have some errors");
              throw new Error("no errors expected in response");
            }
          }
          const errAsString = `${err}`;
          if (errAsString.indexOf("Premature close") !== -1) {
            logger.error(
              "received a premature close from github. retrying request after a pause",
            );
            logger.error(err);
            this.debugLogAnError("github premature close error:", err);
            this._resetTime = DateTime.now().plus({
              milliseconds: 2500 * (i + 1),
            });
            continue;
          }
          throw err;
        }
      }
      throw new Error("too many retries for graphql request");
    }

    async rateLimitedGraphQLGeneratedRequest<
      Input extends object,
      Response,
      R extends GithubGraphQLResponse<{ [key: string]: Response }>,
    >(
      multiplex: MultiplexGithubGraphQLRequester<Input, Response>,
      inputs: Input[],
    ): Promise<MultiplexRequestResponse<R, Response>> {
      try {
        const resp = await multiplex.request(inputs, (r, v) => {
          return this.rateLimitedGraphQLRequest<R>(r, v, true, 2);
        });
        return resp;
      } catch (err) {
        logger.debug("attempt to use smaller batches");
        const responses = await asyncBatchFlattened(
          inputs,
          1,
          async (batch) => {
            const resp = await multiplex.request(batch, (r, v) => {
              return this.rateLimitedGraphQLRequest<R>(r, v, true, 3);
            });
            return [resp];
          },
        );
        return {
          raw: responses.slice(-1)[0].raw,
          items: responses.flatMap((r) => r.items),
        };
      }
    }
  };
}

class _GithubByProjectBaseCollector extends ProjectArtifactsCollector {
  protected recorder: IEventRecorderClient;
  protected cache: TimeSeriesCacheWrapper;
  protected options: GithubBaseCollectorOptions;
  protected resetTime: DateTime | null;
  private requestMutex: Mutex;

  constructor(
    projectRepository: Repository<Project>,
    recorder: IEventRecorderClient,
    cache: TimeSeriesCacheWrapper,
    options: GithubBaseCollectorOptions,
  ) {
    super(projectRepository, recorder, cache, {
      type: In([ArtifactType.GIT_REPOSITORY]),
      namespace: ArtifactNamespace.GITHUB,
    });

    this.options = options;
    this.resetTime = null;
    this.requestMutex = new Mutex();
  }
}

class _GithubBatchedProjectsBaseCollector extends BatchedProjectArtifactsCollector {
  protected recorder: IEventRecorderClient;
  protected cache: TimeSeriesCacheWrapper;
  protected options: GithubBaseCollectorOptions;
  protected resetTime: DateTime | null;

  constructor(
    projectRepository: Repository<Project>,
    recorder: IEventRecorderClient,
    cache: TimeSeriesCacheWrapper,
    batchSize: number,
    options: GithubBaseCollectorOptions,
  ) {
    super(projectRepository, recorder, cache, batchSize, {
      type: In([ArtifactType.GIT_REPOSITORY]),
      namespace: ArtifactNamespace.GITHUB,
    });

    this.options = options;
    this.resetTime = null;
  }
}

class _Base {}

export const GithubBaseMixin = GithubCollectorMixins(_Base);

export const GithubByProjectBaseCollector = GithubCollectorMixins(
  _GithubByProjectBaseCollector,
);
export const GithubBatchedProjectArtifactsBaseCollector = GithubCollectorMixins(
  _GithubBatchedProjectsBaseCollector,
);
