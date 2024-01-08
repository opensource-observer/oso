import {
  StreamKey,
  SyncMode,
  AirbyteStreamBase,
  AirbyteLogger,
} from "faros-airbyte-cdk";
import path from "path";
import { Dictionary } from "ts-essentials";
import _ from "lodash";
import repositorySchema from "../resources/schemas/repository.json" assert { type: "json" };
import { GraphQLClient } from "graphql-request";
import { getOwnerRepos } from "./get-org-repos.js";

type ParseGitHubUrlResult = {
  // e.g. https://github.com/hypercerts-org/oso
  url: string;
  // e.g. 'hypercerts-org/oso'
  slug: string;
  // e.g. 'hypercerts-org'
  owner: string;
  // e.g. 'oso'
  repo?: string;
};

/**
 * Parse a GitHub URL into its owner and name
 * @param url
 * @returns null if invalid input, otherwise the results
 */
function parseGitHubUrl(urlStr: any): ParseGitHubUrlResult | null {
  if (typeof urlStr !== "string") {
    return null;
  }

  try {
    const url = new URL(urlStr);
    const pathParts = url.pathname.split("/").filter((x) => !!x);
    if (!["github.com", "www.github.com"].includes(url.host)) {
      // Check the host
      return null;
    } else if (pathParts.length < 1) {
      // Check if there is a path
      return null;
    } else if (pathParts.length === 1) {
      // If only 1 path part, then it is the owner with no repo
      return {
        url: urlStr,
        slug: pathParts[0],
        owner: pathParts[0],
      };
    } else if (pathParts.length > 1) {
      // Otherwise, take the first 2 parts as the owner and repo
      return {
        url: urlStr,
        slug: `${pathParts[0]}/${pathParts[1]}`,
        owner: pathParts[0],
        repo: path.basename(pathParts[1], ".git"),
      };
    } else {
      // This should never happen
      return null;
    }
  } catch (_e) {
    return null;
  }
}

function isGitHubOrg(urlStr: string) {
  const { owner, repo } = parseGitHubUrl(urlStr) ?? {};
  return !!owner && !repo;
}

function isGitHubRepo(urlStr: string) {
  const { owner, repo } = parseGitHubUrl(urlStr) ?? {};
  return !!owner && !!repo;
}

function isTruthy<T>(value: T): value is _.Truthy<T> {
  return !!value;
}

function filterFalsy<T>(xs: ReadonlyArray<T | null | undefined | false>): T[] {
  return xs.filter(isTruthy);
}

export class Repositories extends AirbyteStreamBase {
  private urls: readonly string[];
  private client: GraphQLClient;

  constructor(
    client: GraphQLClient,
    urls: readonly string[],
    logger: AirbyteLogger,
  ) {
    super(logger);

    this.urls = urls;
    this.client = client;
  }

  getJsonSchema(): Dictionary<any, string> {
    return repositorySchema;
  }

  get primaryKey(): StreamKey {
    return ["url"];
  }

  async *readRecords(
    _syncMode: SyncMode,
    _cursorField?: string[],
    _streamSlice?: Dictionary<any>,
    _streamState?: Dictionary<any>,
  ): AsyncGenerator<Dictionary<any, string>, any, unknown> {
    // Make github requests to find all of the github projects

    const urls = this.urls;
    const repoUrls = urls.filter(isGitHubRepo);
    const orgUrls = urls.filter(isGitHubOrg);

    // Check for invalid URLs
    if (orgUrls.length + repoUrls.length !== urls.length) {
      const nonConfirmingUrls = urls.filter(
        (u) => !isGitHubOrg(u) && !isGitHubRepo(u),
      );
      const sep = "\n\t";
      this.logger.warn(
        `Invalid GitHub URLs:${sep}${nonConfirmingUrls.join(sep)}`,
      );
    }

    // Flatten all GitHub orgs
    const orgNames = filterFalsy(
      orgUrls.map(parseGitHubUrl).map((p) => p?.owner),
    );
    const orgRepos = _.flatten(
      await Promise.all(orgNames.map((o) => getOwnerRepos(this.client, o))),
    );
    const orgRepoUrls = orgRepos.filter((r) => !r.isFork).map((r) => r.url);
    const allRepos = [...repoUrls, ...orgRepoUrls];
    const parsedRepos = allRepos.map(parseGitHubUrl);
    for (const repo of parsedRepos) {
      if (!repo) {
        continue;
      }
      yield {
        owner: `https://github.com/${repo.owner}`,
        name: repo.slug.toLowerCase(),
        url: repo.url,
      };
    }
  }
}
