import { notFound } from "next/navigation";
import { cache } from "react";
import { PlasmicComponent } from "@plasmicapp/loader-nextjs";
import { PLASMIC } from "../../plasmic-init";
import { PlasmicClientRootProvider } from "../../plasmic-init-client";
import { logger } from "../../lib/logger";

const PLASMIC_COMPONENT = "ProjectPage";
export const dynamic = "force-static";
export const revalidate = false; // 3600 = 1 hour

const cachedFetchComponent = cache(async (componentName: string) => {
  try {
    const plasmicData = await PLASMIC.fetchComponentData(componentName);
    return plasmicData;
  } catch (e) {
    logger.warn(e);
    return null;
  }
});

export default async function ProjectPage() {
  // Get Plasmic component
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
      <PlasmicComponent component={compMeta.displayName} />
    </PlasmicClientRootProvider>
  );
}
