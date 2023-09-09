import { notFound } from "next/navigation";
import { PlasmicComponent } from "@plasmicapp/loader-nextjs";
import { PLASMIC } from "../../../plasmic-init";
import { PlasmicClientRootProvider } from "../../../plasmic-init-client";
import { cachedGetProjectBySlug } from "../../../lib/db";
import { logger } from "../../../lib/logger";
import { catchallPathToString } from "../../../lib/paths";

// Using incremental static regeneration, will invalidate this page
// after this (no deploy webhooks needed)
export const revalidate = 3600;
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
  const slug = catchallPathToString(params.slug);
  if (!params.slug || !Array.isArray(params.slug) || params.slug.length < 1) {
    logger.warn("Invalid project page path", params);
    notFound();
  }

  // Get project metadata from the database
  const project = await cachedGetProjectBySlug(slug);
  if (!project) {
    logger.warn(`Cannot find project (slug=${slug})`);
    notFound();
  }

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
          id: project.id,
          metadata: project,
          artifacts: [],
          collections: [],
        }}
      />
    </PlasmicClientRootProvider>
  );
}
