import path from "path";
import _ from "lodash";
import { GraphQLClient } from "graphql-request";
import {
  getOwnerReposRest,
  FullRepository,
  resolveAllReposRest,
} from "./get-org-repos.js";
import { Octokit } from "octokit";

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

export type RepositoryWithParsedUrl = FullRepository & {
  parsedUrl: ParseGitHubUrlResult | null;
};

export async function getReposFromUrls(
  _client: GraphQLClient,
  gh: Octokit,
  urls: string[],
): Promise<RepositoryWithParsedUrl[]> {
  // Make github requests to find all of the github projects

  const repoUrls = urls.filter(isGitHubRepo);
  const orgUrls = urls.filter(isGitHubOrg);

  // Check for invalid URLs
  if (orgUrls.length + repoUrls.length !== urls.length) {
    const nonConfirmingUrls = urls.filter(
      (u) => !isGitHubOrg(u) && !isGitHubRepo(u),
    );
    const sep = "\n\t";
    console.log(`Invalid GitHub URLs:${sep}${nonConfirmingUrls.join(sep)}`);
    // this.logger.warn(
    //   `Invalid GitHub URLs:${sep}${nonConfirmingUrls.join(sep)}`,
    // );
  }

  // Flatten all GitHub orgs
  const orgNames = filterFalsy(
    orgUrls.map(parseGitHubUrl).map((p) => p?.owner),
  );
  const orgRepos = _.flatten(
    await Promise.all(orgNames.map((o) => getOwnerReposRest(gh, o))),
  );

  const parsedRepoUrls = repoUrls.map(parseGitHubUrl);
  const repoSlugs = parsedRepoUrls
    .filter((r) => r !== undefined || r !== null)
    .map((r) => {
      const repo = r!;
      return repo.slug;
    });

  const repos = await resolveAllReposRest(gh, repoSlugs);

  const allRepos = [...repos, ...orgRepos];

  return allRepos.map((r) => {
    const parsed = parseGitHubUrl(r.url);
    return {
      ...r,
      parsedUrl: parsed,
    };
  });
}
