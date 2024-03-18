import { notFound } from "next/navigation";
import { cache } from "react";
import { PlasmicComponent } from "@plasmicapp/loader-nextjs";
import { PLASMIC } from "../../../plasmic-init";
import { PlasmicClientRootProvider } from "../../../plasmic-init-client";
import {
  cachedGetArtifactsByIds,
  cachedGetArtifactIdsByProjectIds,
  cachedGetProjectsBySlugs,
  cachedGetCollectionsByIds,
  cachedGetCollectionIdsByProjectIds,
  cachedGetCodeMetricsByProjectIds,
  cachedGetOnchainMetricsByProjectIds,
  cachedGetAllEventTypes,
} from "../../../lib/graphql/cached-queries";
import { logger } from "../../../lib/logger";
import { catchallPathToString } from "../../../lib/paths";
import { STATIC_EXPORT } from "../../../lib/config";

export const dynamic = STATIC_EXPORT ? "force-static" : "force-dynamic";
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
  const { projects: projectArray } = await cachedGetProjectsBySlugs({
    project_slugs: slugs,
  });
  if (!Array.isArray(projectArray) || projectArray.length < 1) {
    logger.warn(`Cannot find project (slugs=${slugs})`);
    notFound();
  }
  const project = projectArray[0];
  //console.log("project", project);

  const { event_types: eventTypes } = await cachedGetAllEventTypes();
  const { code_metrics_by_project: codeMetrics } =
    await cachedGetCodeMetricsByProjectIds({
      project_ids: [project.project_id],
    });
  const { onchain_metrics_by_project: onchainMetrics } =
    await cachedGetOnchainMetricsByProjectIds({
      project_ids: [project.project_id],
    });
  const { artifacts_by_project: artifactIds } =
    await cachedGetArtifactIdsByProjectIds({
      project_ids: [project.project_id],
    });
  const { projects_by_collection: collectionIds } =
    await cachedGetCollectionIdsByProjectIds({
      project_ids: [project.project_id],
    });
  const { artifacts } = await cachedGetArtifactsByIds({
    artifact_ids: artifactIds.map((x: any) => x.artifact_id),
  });
  const { collections } = await cachedGetCollectionsByIds({
    collection_ids: collectionIds.map((x: any) => x.collection_id),
  });

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
          metadata: project,
          codeMetrics,
          onchainMetrics,
          eventTypes,
          artifacts,
          collections,
        }}
      />
    </PlasmicClientRootProvider>
  );
}
