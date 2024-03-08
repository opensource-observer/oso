import React from "react";
import useSWR from "swr";
import {
  DataProviderView,
  CommonDataProviderRegistration,
} from "./provider-view";
import type { CommonDataProviderProps } from "./provider-view";
import { RegistrationProps } from "../../lib/types/plasmic";

// Default start time
const DEFAULT_START_DATE = 0;
const API_ENDPOINT = "/api/project-event-aggregates";

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

const TableDataProviderRegistration: RegistrationProps<TableDataProviderProps> =
  {
    ...CommonDataProviderRegistration,
    collectionSlugs: {
      type: "array",
      defaultValue: [],
    },
    projectSlugs: {
      type: "array",
      defaultValue: [],
    },
    eventTypes: {
      type: "array",
      defaultValue: [],
    },
    startDate: {
      type: "string",
      helpText: "YYYY-MM-DD",
    },
    endDate: {
      type: "string",
      helpText: "YYYY-MM-DD",
    },
  };

/**
 * TableDataProvider for collections
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

  const querySearchParams = new URLSearchParams();
  if (collectionSlugs && collectionSlugs.length > 0) {
    querySearchParams.append(
      "collectionSlugs",
      collectionSlugs.sort().join(","),
    );
  }
  if (projectSlugs && projectSlugs.length > 0) {
    querySearchParams.append("projectSlugs", projectSlugs.sort().join(","));
  }
  if (eventTypes && eventTypes.length > 0) {
    querySearchParams.append("eventTypes", eventTypes?.sort().join(",") ?? "");
  }
  if (startDate) {
    querySearchParams.append("startDate", startDate);
  }
  if (endDate) {
    querySearchParams.append("endDate", endDate);
  }

  const queryUrl = `${API_ENDPOINT}?${querySearchParams.toString()}`;
  const {
    data: aggregateData,
    error: aggregateError,
    isLoading: aggregateLoading,
  } = useSWR(queryUrl, async () => {
    const response = await fetch(queryUrl);
    return await response.json();
  });

  const formattedData = {
    table: aggregateData,
  };
  //console.log(props.ids, formattedData);
  return (
    <DataProviderView
      {...props}
      formattedData={formattedData}
      loading={aggregateLoading}
      error={aggregateError}
    />
  );
}

export { TableDataProvider, TableDataProviderRegistration };
