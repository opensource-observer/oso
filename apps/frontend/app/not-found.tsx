import { PlasmicComponent } from "@plasmicapp/loader-nextjs";
import { PlasmicClientRootProvider } from "../plasmic-init-client";
import { PLASMIC } from "../plasmic-init";

const PLASMIC_COMPONENT = "404Page";
export const dynamic = "force-static";
export const revalidate = false; // 3600 = 1 hour

export default async function NotFoundPage() {
  const plasmicData = await PLASMIC.fetchComponentData(PLASMIC_COMPONENT);
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
