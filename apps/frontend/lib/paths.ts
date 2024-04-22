/**
 * Joins URI encoded path parts into a string
 * For reference, see https://nextjs.org/docs/app/building-your-application/routing/dynamic-routes#catch-all-segments
 * @param parts comes from a catch-all path from Next.js
 * @returns
 */
const catchallPathToString = (parts: string[]) => {
  return parts.map((p) => decodeURIComponent(p)).join("/");
};

/**
 * Converts a path string to an  enum
 * @param namespacePath
 * @returns
 */
const pathToNamespaceEnum = (namespacePath: string) => {
  switch (namespacePath) {
    case "github":
      return "GITHUB";
    case "gitlab":
      return "GITLAB";
    case "npm":
      return "NPM_REGISTRY";
    case "ethereum":
      return "ETHEREUM";
    case "optimism":
      return "OPTIMISM";
    case "goerli":
      return "GOERLI";
    default:
      return null;
  }
};

/**
 * Converts a path string to an artifact type
 */
const pathToTypeEnum = (typePath: string) => {
  switch (typePath) {
    case "eoa":
      return "EOA_ADDRESS";
    case "repo":
      return "GIT_REPOSITORY";
    default:
      return null;
  }
};

export { catchallPathToString, pathToNamespaceEnum, pathToTypeEnum };
