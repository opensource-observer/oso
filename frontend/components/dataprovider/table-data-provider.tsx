import { useQuery } from "@apollo/experimental-nextjs-app-support/ssr";
import React from "react";
import { DataProviderView } from "./provider-view";
import type { CommonDataProviderProps } from "./provider-view";
import {
  GET_PROJECTS_BY_SLUGS,
  GET_PROJECTS_BY_COLLECTION_SLUGS,
} from "../../lib/graphql/queries";

// Default start time
const DEFAULT_START_DATE = 0;

/**
 * Query component focused on providing data to our data tables
 *
 * Current limitations:
 * - Does not support authentication or RLS. Make sure data is readable by unauthenticated users
 */
type TableDataProviderProps = CommonDataProviderProps & {
  collectionSlugs?: string[]; // Collections to include
  projectSlugs?: string[]; // Projects to include
  eventTypes?: string[];
  startDate?: string;
  endDate?: string;
};

/**
 * EventDataProvider for artifacts
 * @param props
 * @returns
 */
function TableDataProvider(props: TableDataProviderProps) {
  const {
    collectionSlugs,
    projectSlugs,
    eventTypes,
    startDate: rawStartDate,
    endDate,
  } = props;
  const startDate = rawStartDate ?? DEFAULT_START_DATE;

  // Get the project metadata
  const {
    data: projectsByCollectionData,
    error: projectsByCollectionError,
    loading: projectsByCollectionLoading,
  } = useQuery(GET_PROJECTS_BY_COLLECTION_SLUGS, {
    variables: {
      slugs: collectionSlugs ?? [],
    },
  });
  const {
    data: projectsBySlugData,
    error: projectsBySlugError,
    loading: projectsBySlugLoading,
  } = useQuery(GET_PROJECTS_BY_SLUGS, {
    variables: {
      slugs: projectSlugs ?? [],
    },
  });
  const projects = [
    ...(projectsByCollectionData?.project ?? []),
    ...(projectsBySlugData?.project ?? []),
  ];
  console.log(startDate, endDate, eventTypes);

  // Get the aggregate event data
  /**
  const normalizedData: EventData[] = (
    rawData?.events_daily_by_artifact ?? []
  ).map((x) => ({
    type: ensure<string>(x.type, "Data missing 'type'"),
    id: ensure<number>(x.toId, "Data missing 'projectId'"),
    date: ensure<string>(x.bucketDaily, "Data missing 'bucketDaily'"),
    amount: ensure<number>(x.amount, "Data missing 'number'"),
  }));
  console.log(props.ids, rawData, formattedData);
  */
  const formattedData = {
    projects,
  };
  return (
    <DataProviderView
      {...props}
      formattedData={formattedData}
      loading={projectsByCollectionLoading || projectsBySlugLoading}
      error={projectsByCollectionError ?? projectsBySlugError}
    />
  );
}

export { TableDataProvider };
