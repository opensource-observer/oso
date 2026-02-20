import { notFound } from "next/navigation";
import { cache } from "react";
import { PlasmicComponent } from "@plasmicapp/loader-nextjs";
import { PLASMIC } from "@/plasmic-init";
import { PlasmicClientRootProvider } from "@/plasmic-init-client";
import { AppApolloWrapper } from "@/components/dataprovider/app-apollo-wrapper";
import { logger } from "@/lib/logger";

const PLASMIC_COMPONENT = "LayoutApp";

const cachedFetchComponent = cache(async (componentName: string) => {
  try {
    const plasmicData = await PLASMIC.fetchComponentData(componentName);
    return plasmicData;
  } catch (e) {
    logger.warn(e);
    return null;
  }
});

export default async function PlasmicLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: { orgName: string };
}) {
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
          children: <AppApolloWrapper>{children}</AppApolloWrapper>,
          activeOrgName: params.orgName,
        }}
      />
    </PlasmicClientRootProvider>
  );
}
