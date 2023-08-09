import path from "path";

type ParseGitHubUrlResult = {
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
        slug: pathParts[0],
        owner: pathParts[0],
      };
    } else if (pathParts.length > 1) {
      // Otherwise, take the first 2 parts as the owner and repo
      return {
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

type ParseNpmUrlResult = {
  // e.g. '@hypercerts-org/oso'
  slug: string;
  // e.g. '@hypercerts-org'
  scope?: string;
};

/**
 *
 * Parse an npm URL into its scope and name
 * @param url
 * @returns null if invalid input, otherwise the results
 */
function parseNpmUrl(urlStr: any): ParseNpmUrlResult | null {
  if (typeof urlStr !== "string") {
    return null;
  }

  try {
    const url = new URL(urlStr);
    const pathParts = url.pathname.split("/").filter((x) => !!x);
    if (!["npmjs.com", "www.npmjs.com"].includes(url.host)) {
      // Check the host
      return null;
    } else if (pathParts.length < 1) {
      // Check for a valid path
      return null;
    } else if (pathParts.length === 1) {
      // If only 1 path part, then it is the slug
      return {
        slug: pathParts[0],
      };
    } else if (pathParts[0] !== "package") {
      // If there are more than 2 parts, the first part must be "package"
      return null;
    } else if (pathParts.length === 2) {
      // If there are 2 parts, then the slug is the second part
      return {
        slug: pathParts[1],
      };
    } else if (pathParts.length > 2) {
      // Otherwise, the scope is the first part and the slug is the first 2
      return {
        slug: `${pathParts[1]}/${pathParts[2]}`,
        scope: pathParts[1],
      };
    } else {
      // This should never happen
      return null;
    }
  } catch (_e) {
    return null;
  }
}

export { ParseGitHubUrlResult, parseGitHubUrl, ParseNpmUrlResult, parseNpmUrl };
