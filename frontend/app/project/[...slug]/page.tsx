import { notFound } from "next/navigation";
import { cache } from "react";
import { PlasmicComponent } from "@plasmicapp/loader-nextjs";
import { PLASMIC } from "../../../plasmic-init";
import { PlasmicClientRootProvider } from "../../../plasmic-init-client";
import { cachedGetProjectsBySlugs } from "../../../lib/graphql/cached-queries";
import { logger } from "../../../lib/logger";
import { catchallPathToString } from "../../../lib/paths";

export const revalidate = false; // 3600 = 1 hour
const STATIC_EXPORT_SLUGS = ["IGNORE"];
const PLASMIC_COMPONENT = "ProjectPage";

const cachedFetchComponent = cache(async (componentName: string) => {
  const plasmicData = await PLASMIC.fetchComponentData(componentName);
  return plasmicData;
});

export async function generateStaticParams() {
  return STATIC_EXPORT_SLUGS.map((s) => ({
    slug: [s],
  }));
}

/**
 * This SSR route allows us to fetch the project from the database
 * on the first HTTP request, which should be faster than fetching it client-side
 */

type ProjectPageProps = {
  params: {
    slug: string[];
  };
  //searchParams?: Record<string, string | string[]>;
};

export default async function ProjectPage(props: ProjectPageProps) {
  const { params } = props;
  const slugs = [catchallPathToString(params.slug)];
  if (!params.slug || !Array.isArray(params.slug) || params.slug.length < 1) {
    logger.warn("Invalid project page path", params);
    notFound();
  }

  // Get project metadata from the database
  const { project: projectArray } = await cachedGetProjectsBySlugs({ slugs });
  if (!Array.isArray(projectArray) || projectArray.length < 1) {
    logger.warn(`Cannot find project (slugs=${slugs})`);
    notFound();
  }
  const project = projectArray[0];

  //console.log(project);
  const plasmicData = await cachedFetchComponent(PLASMIC_COMPONENT);
  const compMeta = plasmicData.entryCompMetas[0];

  return (
    <PlasmicClientRootProvider
      prefetchedData={plasmicData}
      pageParams={compMeta.params}
    >
      <PlasmicComponent
        component={compMeta.displayName}
        componentProps={{
          metadata: project,
        }}
      />
    </PlasmicClientRootProvider>
  );
}
