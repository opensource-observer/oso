import { PlasmicComponent } from "@plasmicapp/loader-nextjs";
import { PLASMIC } from "../plasmic-init";
import { PlasmicClientRootProvider } from "../plasmic-init-client";

// Using incremental static regeneration, will invalidate this page
// after this (no deploy webhooks needed)
export const dynamic = "force-static";
export const revalidate = false; // 3600 = 1 hour
const PLASMIC_COMPONENT = "Homepage";

export default async function HomePage() {
  //console.log(project);
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
