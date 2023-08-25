import { notFound } from "next/navigation";
import { ArtifactNamespace } from "@hypercerts-org/indexer";
import { cachedGetArtifactByName } from "../../../../../lib/db";
import { logger } from "../../../../../lib/logger";
import { catchallPathToString } from "../../../../../lib/paths";

/**
 * TODO: This SSR route allows us to fetch the project from the database
 * on the first HTTP request, which should be faster than fetching it client-side
 */

/**
 * Converts a path string to an ArtifactNamespace enum
 * @param namespacePath
 * @returns
 */
const pathToNamespaceEnum = (namespacePath: string) => {
  switch (namespacePath) {
    case "github":
      return ArtifactNamespace.GITHUB;
    case "gitlab":
      return ArtifactNamespace.GITLAB;
    case "npm":
      return ArtifactNamespace.NPM_REGISTRY;
    case "ethereum":
      return ArtifactNamespace.ETHEREUM;
    case "optimism":
      return ArtifactNamespace.OPTIMISM;
    case "goerli":
      return ArtifactNamespace.GOERLI;
    default:
      return null;
  }
};

type ArtifactPageProps = {
  params: {
    namespace: string;
    name: string[];
  };
};

export default async function ArtifactPage(props: ArtifactPageProps) {
  const { params } = props;
  const namespace = pathToNamespaceEnum(params.namespace);
  const name = catchallPathToString(params.name);
  if (
    !params.namespace ||
    !params.name ||
    !Array.isArray(params.name) ||
    params.name.length < 1 ||
    !namespace
  ) {
    logger.warn("Invalid artifact page path", params);
    notFound();
  }

  // Get artifact metadata from the database
  const artifact = await cachedGetArtifactByName({ namespace, name });
  if (!artifact) {
    logger.warn(`Cannot find artifact (namespace=${namespace}, name=${name})`);
    notFound();
  }

  console.log(artifact);

  // TODO: render the Plasmic page
  return (
    <div>
      My Path: {namespace} / {name}
    </div>
  );
}
