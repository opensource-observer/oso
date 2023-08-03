export interface ParseGitHubUrlResult {
  owner: string;
  name?: string;
}

/**
 * Parse a GitHub URL into its owner and name
 * @param url
 * @returns null if invalid input, otherwise the results
 */
export function parseGithubUrl(url: any): ParseGitHubUrlResult | null {
  if (typeof url !== "string") {
    return null;
  }

  // eslint-disable-next-line no-useless-escape
  const regex = /\/\/github.com\/([^/]+)(\/([^\./]+))?/g;
  const matches = regex.exec(url);
  if (!matches || matches.length < 2) {
    return null;
  }

  const owner = matches[1];
  const name = matches[3];

  if (!owner) {
    return null;
  }

  return {
    owner,
    name,
  };
}
