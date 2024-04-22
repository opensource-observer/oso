import { notFound } from "next/navigation";
import { cache } from "react";
import { PlasmicComponent } from "@plasmicapp/loader-nextjs";
import { PLASMIC } from "../../../../../plasmic-init";
import { PlasmicClientRootProvider } from "../../../../../plasmic-init-client";
import { cachedGetArtifactByName } from "../../../../../lib/graphql/cached-queries";
import { logger } from "../../../../../lib/logger";
import {
  catchallPathToString,
  pathToNamespaceEnum,
  pathToTypeEnum,
} from "../../../../../lib/paths";

const PLASMIC_COMPONENT = "ArtifactPage";
//export const dynamic = STATIC_EXPORT ? "force-static" : "force-dynamic";
export const dynamic = "force-static";
export const dynamicParams = true;
export const revalidate = false; // 3600 = 1 hour
// TODO: This cannot be empty due to this bug
// https://github.com/vercel/next.js/issues/61213
const STATIC_EXPORT_PARAMS = [
  {
    namespace: "github",
    type: "repo",
    name: ["opensource-observer", "oso"],
  },
];
export async function generateStaticParams() {
  return STATIC_EXPORT_PARAMS;
}

const cachedFetchComponent = cache(async (componentName: string) => {
  try {
    const plasmicData = await PLASMIC.fetchComponentData(componentName);
    return plasmicData;
  } catch (e) {
    logger.warn(e);
    return null;
  }
});

/**
 * This SSR route allows us to fetch the project from the database
 * on the first HTTP request, which should be faster than fetching it client-side
 */

type ArtifactPageProps = {
  params: {
    namespace: string;
    type: string;
    name: string[];
  };
};

export default async function ArtifactPage(props: ArtifactPageProps) {
  const { params } = props;
  const namespace = pathToNamespaceEnum(params.namespace);
  const type = pathToTypeEnum(params.type);
  const name = catchallPathToString(params.name);
  if (
    !params.namespace ||
    !params.type ||
    !params.name ||
    !Array.isArray(params.name) ||
    params.name.length < 1 ||
    !namespace ||
    !type
  ) {
    logger.warn("Invalid artifact page path", params);
    notFound();
  }

  // Get artifact metadata from the database
  const { artifacts: artifactArray } = await cachedGetArtifactByName({
    artifact_namespace: namespace,
    artifact_type: type,
    artifact_name: name,
  });
  if (!Array.isArray(artifactArray) || artifactArray.length < 1) {
    logger.warn(`Cannot find artifact (namespace=${namespace}, name=${name})`);
    notFound();
  }
  const artifact = artifactArray[0];

  //console.log(artifact);
  const plasmicData = await cachedFetchComponent(PLASMIC_COMPONENT);
  if (!plasmicData) {
    logger.warn(`Unable to get componentName=${PLASMIC_COMPONENT}`);
    notFound();
  }
  const compMeta = plasmicData.entryCompMetas[0];

  return (
    <PlasmicClientRootProvider
      prefetchedData={plasmicData}
      pageParams={compMeta.params}
    >
      <PlasmicComponent
        component={compMeta.displayName}
        componentProps={{
          metadata: artifact,
        }}
      />
    </PlasmicClientRootProvider>
  );
}
