import { notFound } from "next/navigation";
import { cache } from "react";
import { PlasmicComponent } from "@plasmicapp/loader-nextjs";
import { PLASMIC } from "../../../plasmic-init";
import { PlasmicClientRootProvider } from "../../../plasmic-init-client";
import { cachedGetMetricByName } from "../../../lib/clickhouse/cached-queries";
import { logger } from "../../../lib/logger";
import { catchallPathToString } from "../../../lib/paths";

const METRIC_SOURCE = "OSO";
const METRIC_NAMESPACE = "oso";
const PLASMIC_COMPONENT = "MetricPage";
//export const dynamic = STATIC_EXPORT ? "force-static" : "force-dynamic";
//export const dynamic = "force-static";
export const dynamic = "force-dynamic";
export const dynamicParams = true;
export const revalidate = false; // 3600 = 1 hour
// TODO: This cannot be empty due to this bug
// https://github.com/vercel/next.js/issues/61213
const STATIC_EXPORT_SLUGS: string[] = ["stars"];
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
 * This SSR route allows us to fetch the metric from the database
 * on the first HTTP request, which should be faster than fetching it client-side
 */

type MetricPagePath = {
  name: string[];
};

type MetricPageProps = {
  params: MetricPagePath;
};

export default async function MetricPage(props: MetricPageProps) {
  const { params } = props;
  if (!params.name || !Array.isArray(params.name) || params.name.length < 1) {
    logger.warn("Invalid metric page path", params);
    notFound();
  }

  // Get metric metadata from the database
  const name = catchallPathToString(params.name);
  const metricArray = await cachedGetMetricByName({
    metricSource: METRIC_SOURCE,
    metricNamespace: METRIC_NAMESPACE,
    metricName: name,
  });
  if (!Array.isArray(metricArray) || metricArray.length < 1) {
    logger.warn(`Cannot find metric (name=${name})`);
    notFound();
  }
  const metadata = metricArray[0];
  //console.log("project", project);

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
          metadata,
        }}
      />
    </PlasmicClientRootProvider>
  );
}
