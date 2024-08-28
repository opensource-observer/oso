import { notFound, redirect } from "next/navigation";
import { cache } from "react";
import { PlasmicComponent } from "@plasmicapp/loader-nextjs";
import { PLASMIC } from "../../../plasmic-init";
import { PlasmicClientRootProvider } from "../../../plasmic-init-client";
import {
  cachedGetCollectionByName,
  cachedGetCodeMetricsByProjectIds,
  cachedGetOnchainMetricsByProjectIds,
  cachedGetProjectIdsByCollectionName,
} from "../../../lib/clickhouse/cached-queries";
import { logger } from "../../../lib/logger";
import { catchallPathToString } from "../../../lib/paths";

const COLLECTION_SOURCE = "OSS_DIRECTORY";
const COLLECTION_NAMESPACE = "oso";
const RETRY_URL = "/retry";
const PLASMIC_COMPONENT = "CollectionPage";
//export const dynamic = STATIC_EXPORT ? "force-static" : "force-dynamic";
//export const dynamic = "force-static";
export const dynamic = "force-dynamic";
export const dynamicParams = true;
export const revalidate = false; // 3600 = 1 hour
// TODO: This cannot be empty due to this bug
// https://github.com/vercel/next.js/issues/61213
const STATIC_EXPORT_SLUGS: string[] = ["optimism"];
export async function generateStaticParams() {
  return STATIC_EXPORT_SLUGS.map((s) => ({
    name: [s],
  }));
}

const cachedFetchComponent = cache(async (componentName: string) => {
  try {
    const plasmicData = await PLASMIC.fetchComponentData(componentName);
    return plasmicData;
  } catch (e) {
    logger.warn(e);
    return null;
  }
});

/**
 * This SSR route allows us to fetch the project from the database
 * on the first HTTP request, which should be faster than fetching it client-side
 */

type CollectionPagePath = {
  name: string[];
};

type CollectionPageProps = {
  params: CollectionPagePath;
};

export default async function CollectionPage(props: CollectionPageProps) {
  const { params } = props;
  if (!params.name || !Array.isArray(params.name) || params.name.length < 1) {
    logger.warn("Invalid collection page path", params);
    notFound();
  }

  try {
    // Get project metadata from the database
    const name = catchallPathToString(params.name);
    const data1 = await Promise.all([
      await cachedGetCollectionByName({
        collectionSource: COLLECTION_SOURCE,
        collectionNamespace: COLLECTION_NAMESPACE,
        collectionName: name,
      }),
      await cachedGetProjectIdsByCollectionName({
        collectionSource: COLLECTION_SOURCE,
        collectionNamespace: COLLECTION_NAMESPACE,
        collectionName: name,
      }),
    ]);
    const collectionArray = data1[0];
    const projectIdArray = data1[1];
    if (
      !Array.isArray(collectionArray) ||
      collectionArray.length < 1 ||
      !Array.isArray(projectIdArray)
    ) {
      logger.warn(`Cannot find collection (name=${name})`);
      notFound();
    }
    const collection = collectionArray[0];
    //console.log("project", project);

    // Parallelize getting things related to the project
    const projectIds = projectIdArray.map((x) => x.project_id);
    const data2 = await Promise.all([
      cachedGetCodeMetricsByProjectIds({
        projectIds,
      }),
      cachedGetOnchainMetricsByProjectIds({
        projectIds,
      }),
    ]);
    const codeMetrics = data2[0];
    const onchainMetrics = data2[1];

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
        <PlasmicComponent
          component={compMeta.displayName}
          componentProps={{
            metadata: collection,
            codeMetrics,
            onchainMetrics,
          }}
        />
      </PlasmicClientRootProvider>
    );
  } catch (_e) {
    // Most likely caused by database timing out
    redirect(RETRY_URL);
  }
}
