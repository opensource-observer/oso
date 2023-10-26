import { notFound } from "next/navigation";
import { PlasmicComponent } from "@plasmicapp/loader-nextjs";
import { PLASMIC } from "../../../plasmic-init";
import { PlasmicClientRootProvider } from "../../../plasmic-init-client";
import { cachedGetProjectsBySlugs } from "../../../lib/graphql/cached-queries";
import { logger } from "../../../lib/logger";
import { catchallPathToString } from "../../../lib/paths";

// Using incremental static regeneration, will invalidate this page
// after this (no deploy webhooks needed)
export const revalidate = 86400; // 3600 = 1 hour
const PLASMIC_COMPONENT = "ProjectPage";

/**
 * This SSR route allows us to fetch the project from the database
 * on the first HTTP request, which should be faster than fetching it client-side
 */

type ProjectPageProps = {
  params: {
    slug: string[];
  };
  searchParams?: Record<string, string | string[]>;
};

export default async function ProjectPage(props: ProjectPageProps) {
  const { params, searchParams } = props;
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
          metadata: project,
        }}
      />
    </PlasmicClientRootProvider>
  );
}
