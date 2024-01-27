import { notFound } from "next/navigation";
import { cache } from "react";
import { PlasmicComponent } from "@plasmicapp/loader-nextjs";
import { PLASMIC } from "../../../../plasmic-init";
import { PlasmicClientRootProvider } from "../../../../plasmic-init-client";
import { cachedGetArtifactByName } from "../../../../lib/graphql/cached-queries";
import { logger } from "../../../../lib/logger";
import {
  catchallPathToString,
  pathToNamespaceEnum,
} from "../../../../lib/paths";
import { STATIC_EXPORT } from "../../../../lib/config";

// Using incremental static regeneration, will invalidate this page
// after this (no deploy webhooks needed)
export const dynamic = STATIC_EXPORT ? "force-static" : "force-dynamic";
export const revalidate = false; // 3600 = 1 hour
const STATIC_EXPORT_PARAMS = [
  {
    namespace: "IGNORE",
    name: ["IGNORE"],
  },
];
const PLASMIC_COMPONENT = "ArtifactPage";

const cachedFetchComponent = cache(async (componentName: string) => {
  const plasmicData = await PLASMIC.fetchComponentData(componentName);
  return plasmicData;
});

export async function generateStaticParams() {
  return STATIC_EXPORT_PARAMS;
}

/**
 * This SSR route allows us to fetch the project from the database
 * on the first HTTP request, which should be faster than fetching it client-side
 */

type ArtifactPageProps = {
  params: {
    namespace: string;
    name: string[];
  };
  searchParams?: Record<string, string | string[]>;
};

export default async function ArtifactPage(props: ArtifactPageProps) {
  const { params, searchParams } = props;
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
  const { artifact: artifactArray } = await cachedGetArtifactByName({
    namespace,
    name,
  });
  if (!Array.isArray(artifactArray) || artifactArray.length < 1) {
    logger.warn(`Cannot find artifact (namespace=${namespace}, name=${name})`);
    notFound();
  }
  const artifact = artifactArray[0];

  //console.log(artifact);
  const plasmicData = await cachedFetchComponent(PLASMIC_COMPONENT);
  const compMeta = plasmicData.entryCompMetas[0];

  return (
    <PlasmicClientRootProvider
      prefetchedData={plasmicData}
      pageParams={compMeta.params}
      pageQuery={searchParams}
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
