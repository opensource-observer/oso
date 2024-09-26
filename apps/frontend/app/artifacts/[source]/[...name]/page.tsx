import { notFound } from "next/navigation";
import _ from "lodash";
import { cache } from "react";
import { PlasmicComponent } from "@plasmicapp/loader-nextjs";
import { PLASMIC } from "../../../../plasmic-init";
import { PlasmicClientRootProvider } from "../../../../plasmic-init-client";
import {
  cachedGetArtifactByName,
  cachedGetCodeMetricsByArtifactIds,
} from "../../../../lib/clickhouse/cached-queries";
import { logger } from "../../../../lib/logger";

const PLASMIC_COMPONENT = "ArtifactPage";
//export const dynamic = STATIC_EXPORT ? "force-static" : "force-dynamic";
export const dynamic = "force-dynamic";
export const dynamicParams = true;
export const revalidate = false; // 3600 = 1 hour
/**
// TODO: This cannot be empty due to this bug
// https://github.com/vercel/next.js/issues/61213
const STATIC_EXPORT_PARAMS: ArtifactPagePath[] = [
  {
    source: "github",
    name: ["opensource-observer", "oso"],
  },
];
export async function generateStaticParams() {
  return STATIC_EXPORT_PARAMS;
}
 */

async function getDefaultProps() {
  return {
    keyMetrics: [],
    metricChoices: [],
  };
}

async function getCodeProps(artifactId: string) {
  const codeMetrics = await cachedGetCodeMetricsByArtifactIds({
    artifactIds: [artifactId],
  });
  const keyMetrics = [
    {
      title: "Star Count",
      subtitle: "For the repository",
      value: _.sumBy(codeMetrics, "star_count"),
    },
    {
      title: "Forks",
      subtitle: "For the repository",
      value: _.sumBy(codeMetrics, "fork_count"),
    },
    {
      title: "Total Contributors",
      subtitle: "All time",
      value: _.sumBy(codeMetrics, "contributor_count"),
    },
    {
      title: "Active Contributors",
      subtitle: "Who have been active in last 6 months",
      value: _.sumBy(codeMetrics, "contributor_count_6_months"),
    },
    {
      title: "New Contributors",
      subtitle: "Who joined in last 6 months",
      value: _.sumBy(codeMetrics, "new_contributor_count_6_months"),
    },
    {
      title: "Active Developers",
      subtitle: "Who committed code in last 6 months",
      value: _.sumBy(codeMetrics, "active_developer_count_6_months"),
    },
    {
      title: "Recent Commits",
      subtitle: "Commits within the last 6 months",
      value: _.sumBy(codeMetrics, "commit_count_6_months"),
    },
  ];
  const metricChoices = [
    {
      label: "Active Developers (30d)",
      value: "0x9o4M40uii5KDWi3B5OQLk97SgpZw81aDpL53a/g+c=",
      selected: true,
    },
    {
      label: "Parttime Developers (30d)",
      value: "j639+oJeAtYFJvaMjF9JHGfw7U/2u3L9XlErnrLKLhQ=",
      selected: false,
    },
    {
      label: "Fulltime Developers (30d)",
      value: "vlFMX++GcaW2nPGuwTs+PMXFqlr/s3tnTzG1n7gXyx8=",
      selected: false,
    },
    {
      label: "Commits",
      value: "Oh9Xi1a2ovZScVN77o1ye4sInynC4t3yQoWvvHdqkdQ=",
      selected: true,
    },
    {
      label: "Forks",
      value: "tx4sCflOBp/pKjncprKr9FGuhTgeaj3hnpIzTON650g=",
      selected: false,
    },
    {
      label: "Stars",
      value: "SrsN3Wc2CSLRktIZB+RqPXGoH4o7nj7s23tm+skPZzw=",
      selected: true,
    },
  ];

  return {
    keyMetrics,
    metricChoices,
  };
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

type ArtifactPagePath = {
  source: string;
  name: string[];
};

type ArtifactPageProps = {
  params: ArtifactPagePath;
};

export default async function ArtifactPage(props: ArtifactPageProps) {
  const { params } = props;

  if (
    !params.source ||
    !params.name ||
    !Array.isArray(params.name) ||
    params.name.length < 1
  ) {
    logger.warn("Invalid artifact page path", params);
    notFound();
  }

  const source = params.source.toUpperCase();
  const [namespace, name] =
    params.name.length > 1 ? params.name : [undefined, params.name[0]];

  // Get artifact metadata from the database
  const artifactArray = await cachedGetArtifactByName({
    artifactSource: source,
    artifactNamespace: namespace,
    artifactName: name,
  });
  if (!Array.isArray(artifactArray) || artifactArray.length < 1) {
    logger.warn(
      `Cannot find artifact (source=${source}, namespace=${namespace}, name=${name})`,
    );
    notFound();
  }
  const artifact = artifactArray[0];
  const artifactId = artifact.artifact_id;
  const metricProps =
    source === "GITHUB"
      ? await getCodeProps(artifactId)
      : await getDefaultProps();

  //console.log(artifact);
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
          metadata: artifact,
          ...metricProps,
        }}
      />
    </PlasmicClientRootProvider>
  );
}
