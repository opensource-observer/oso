import { notFound } from "next/navigation";
import { ArtifactNamespace } from "@opensource-observer/indexer";
import { PlasmicComponent } from "@plasmicapp/loader-nextjs";
import { PLASMIC } from "../../../../plasmic-init";
import { PlasmicClientRootProvider } from "../../../../plasmic-init-client";
import { cachedGetArtifactByName } from "../../../../lib/db";
import { logger } from "../../../../lib/logger";
import { catchallPathToString } from "../../../../lib/paths";
import { uncheckedCast } from "../../../../lib/common";

// Using incremental static regeneration, will invalidate this page
// after this (no deploy webhooks needed)
export const revalidate = 3600;
const PLASMIC_COMPONENT = "ArtifactPage";

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
  const namespace = uncheckedCast<ArtifactNamespace>(params.namespace);
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

  //console.log(artifact);
  const plasmicData = await PLASMIC.fetchComponentData(PLASMIC_COMPONENT);
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
          id: artifact.id,
          metadata: artifact,
        }}
      />
    </PlasmicClientRootProvider>
  );
}
