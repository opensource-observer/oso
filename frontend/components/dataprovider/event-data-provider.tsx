import { useQuery } from "@apollo/experimental-nextjs-app-support/ssr";
import dayjs from "dayjs";
import _ from "lodash";
import React from "react";
import { assertNever, ensure, uncheckedCast } from "../../lib/common";
import {
  GET_ARTIFACTS_BY_IDS,
  GET_EVENTS_DAILY_TO_ARTIFACT,
  GET_EVENTS_DAILY_TO_PROJECT,
  GET_PROJECTS_BY_IDS,
} from "../../lib/graphql/queries";
import { DataProviderView } from "./provider-view";
import type { CommonDataProviderProps } from "./provider-view";

// TO FIX BUILDS WE ARE HARDCODING THE EVENT TYPES FOR NOW. THIS SHOULD INSTEAD
// CALL THE DATABASE FOR THESE VALUES (AND CACHE THEM)
const EVENT_TYPE_NAME_TO_ID: Record<string, number> = {
  FUNDING: 1,
  PULL_REQUEST_CREATED: 2,
  PULL_REQUEST_MERGED: 3,
  COMMIT_CODE: 4,
  ISSUE_FILED: 5,
  ISSUE_CLOSED: 6,
  DOWNSTREAM_DEPENDENCY_COUNT: 7,
  UPSTREAM_DEPENDENCY_COUNT: 8,
  DOWNLOADS: 9,
  CONTRACT_INVOKED: 10,
  USERS_INTERACTED: 11,
  CONTRACT_INVOKED_AGGREGATE_STATS: 12,
  PULL_REQUEST_CLOSED: 13,
  STAR_AGGREGATE_STATS: 14,
  PULL_REQUEST_REOPENED: 15,
  PULL_REQUEST_REMOVED_FROM_PROJECT: 16,
  PULL_REQUEST_APPROVED: 17,
  ISSUE_CREATED: 18,
  ISSUE_REOPENED: 19,
  ISSUE_REMOVED_FROM_PROJECT: 20,
  STARRED: 21,
  FORK_AGGREGATE_STATS: 22,
  FORKED: 23,
  WATCHER_AGGREGATE_STATS: 24,
  CONTRACT_INVOCATION_DAILY_COUNT: 25,
  CONTRACT_INVOCATION_DAILY_FEES: 26,
};
const EVENT_TYPE_ID_TO_NAME = _.invert(EVENT_TYPE_NAME_TO_ID);

type ChartType = "areaChart" | "barList";
type XAxis = "eventTime" | "entity" | "eventType";
type EntityType = "project" | "artifact";

// Default start time
const DEFAULT_START_DATE = 0;
// Default XAxis if not specified
const DEFAULT_XAXIS: XAxis = "eventType";

/**
 * Regardless of the data query, this will be the intermediate
 * format we need to normalize against before we put it into the
 * data formatters (for charts)
 **/
type EventData = {
  typeId: number;
  id: number;
  date: string;
  amount: number;
};

/**
 * Abstract entity data that could come from either an `Artifact` or `Project`
 */
type EntityData = {
  id: number;
  name: string;
};

/**
 * Query component focused on providing data to visualiation components
 *
 * Current limitations:
 * - Does not support authentication or RLS. Make sure data is readable by unauthenticated users
 */
type EventDataProviderProps = CommonDataProviderProps & {
  chartType: ChartType;
  xAxis?: XAxis; // X-axis
  entityType?: EntityType;
  ids?: string[];
  eventTypes?: string[];
  startDate?: string;
  endDate?: string;
};

/**
 * Convert the event time to a date label
 */
const eventTimeToLabel = (t: any) => dayjs(t).format("YYYY-MM-DD");

/**
 * If we get enums (e.g. NPM_PACKAGE), normalize it into a readable label
 * @param t
 * @returns
 */
const eventTypeToLabel = (t: string) => _.capitalize(t.replace(/_/g, " "));

/**
 * Given an id, try to find the id in EntityData[] and return the name
 * Note: the `==` is intentional here, since we may be comparing a string to a number
 */
const entityIdToLabel = (id: number | string, entityData?: EntityData[]) =>
  entityData?.find((x) => x.id == id)?.name ?? id;

/**
 * Formats normalized data into inputs to an area chart (for Tremor)
 * @param data
 * @returns
 */
const formatDataToAreaChart = (
  data: EventData[],
  categories: { results: string[]; opts: CategoryOpts },
  entityData?: EntityData[],
) => {
  // Start with an empty data point for each available date
  const emptyDataPoint = _.fromPairs(categories.results.map((c) => [c, 0]));
  const datesWithData = _.uniq(data.map((x) => eventTimeToLabel(x.date)));
  const groupedByDate = _.fromPairs(
    datesWithData.map((d) => [d, _.clone(emptyDataPoint)]),
  );
  //console.log(groupedByDate);

  // Sum the values for each (date, artifactId, eventType)
  data.forEach((d) => {
    const dateLabel = eventTimeToLabel(d.date);
    const category = createCategory(
      d.id,
      EVENT_TYPE_ID_TO_NAME[d.typeId],
      entityData,
      categories.opts,
    );
    groupedByDate[dateLabel][category] += d.amount;
  });
  //console.log(groupedByDate);

  // Flatten into an array
  const unsorted = _.toPairs(groupedByDate).map((x) => ({
    ...x[1],
    date: x[0],
  }));
  //console.log(unsorted);

  // Sort by date
  const result = _.sortBy(unsorted, (x) => x.date);
  //console.log(result);

  // Trim empty data at the start and end
  const isEmptyDataPoint = (x: _.Dictionary<number | string>): boolean => {
    for (const cat of categories.results) {
      if (x[cat] !== 0) {
        return false;
      }
    }
    return true;
  };
  let [i, j] = [0, result.length - 1];
  while (i < result.length && isEmptyDataPoint(result[i])) {
    i++;
  }
  while (j > 0 && isEmptyDataPoint(result[j])) {
    j--;
  }
  const slicedResult = result.slice(i, j + 1);

  // Fill in any empty dates
  let currDate = dayjs(result[0]?.date);
  const filledResult = [];
  for (const x of slicedResult) {
    const thisDate = dayjs(x.date);
    while (currDate.isBefore(thisDate)) {
      filledResult.push({
        ...emptyDataPoint,
        date: currDate.format("YYYY-MM-DD"),
      });
      currDate = currDate.add(1, "day");
    }
    filledResult.push(x);
    currDate = thisDate.add(1, "day");
  }
  //console.log(filledResult);

  return {
    data: filledResult,
    categories: categories.results,
    xAxis: "date",
  };
};

/**
 * Formats normalized data for a bar chart (for Tremor)
 * @param xAxis
 * @param data
 * @returns
 */
const formatDataToBarList = (
  xAxis: XAxis,
  data: EventData[],
  entityData?: EntityData[],
) => {
  const grouped = _.groupBy(data, (x) =>
    xAxis === "eventTime"
      ? x.date
      : xAxis === "entity"
      ? x.id
      : xAxis === "eventType"
      ? EVENT_TYPE_ID_TO_NAME[x.typeId]
      : assertNever(xAxis),
  );
  const summed = _.mapValues(grouped, (x) => _.sumBy(x, (x) => x.amount));
  const result = _.toPairs(summed).map((x) => ({
    name:
      xAxis === "eventTime"
        ? eventTimeToLabel(x[0])
        : xAxis === "entity"
        ? entityIdToLabel(x[0], entityData)
        : xAxis === "eventType"
        ? eventTypeToLabel(x[0])
        : assertNever(xAxis),
    value: x[1],
  }));
  return {
    data: result,
  };
};

/**
 * Parses string IDs into integers
 * @param ids
 * @returns
 */
const stringToIntArray = (ids?: string[]): number[] =>
  ids?.map((id) => parseInt(id)).filter((id) => !!id && !isNaN(id)) ?? [];

type CategoryOpts = {
  includeIds?: boolean;
  includeTypes?: boolean;
};

/**
 * TODO: Creates unique categories for the area chart
 * - Currently, we just use the type, which will merge data across IDs
 * - We need to add unique identifiers for each ID to properly segregate
 * @param entityType
 * @param id
 * @param type
 * @returns
 */
const createCategory = (
  id: number,
  type: string,
  entityData?: EntityData[],
  opts?: CategoryOpts,
) => {
  if (opts?.includeIds && opts?.includeTypes) {
    return `${entityIdToLabel(id, entityData)}: ${eventTypeToLabel(type)}`;
  } else if (opts?.includeIds) {
    return `${entityIdToLabel(id, entityData)}`;
  } else {
    return `${eventTypeToLabel(type)}`;
  }
};

const createCategories = (
  props: EventDataProviderProps,
  entityData?: EntityData[],
) => {
  const ids = stringToIntArray(props.ids);
  const types = props.eventTypes ?? [];
  const results: string[] = [];
  const opts: CategoryOpts = {
    includeIds: ids.length > 1,
    includeTypes: types.length > 1,
  };
  for (const id of ids) {
    for (const type of types) {
      results.push(createCategory(id, type, entityData, opts));
    }
  }
  return {
    results,
    opts,
  };
};

/**
 * Switches on the props to return formatted data
 * @param props - component props
 * @param rawData - normalized data from a GraphQL query
 * @returns
 */
const formatData = (
  props: EventDataProviderProps,
  rawData: EventData[],
  entityData?: EntityData[],
) => {
  //const checkedData = rawData as unknown as EventData[];
  // Short-circuit if test data
  const data = props.useTestData
    ? uncheckedCast<EventData[]>(props.testData)
    : rawData;

  const formattedData =
    props.chartType === "areaChart"
      ? formatDataToAreaChart(
          data,
          createCategories(props, entityData),
          entityData,
        )
      : props.chartType === "barList"
      ? formatDataToBarList(props.xAxis ?? DEFAULT_XAXIS, data, entityData)
      : assertNever(props.chartType);
  return formattedData;
};

/**
 * EventDataProvider for artifacts
 * @param props
 * @returns
 */
function ArtifactEventDataProvider(props: EventDataProviderProps) {
  const {
    data: rawEventData,
    error: eventError,
    loading: eventLoading,
  } = useQuery(GET_EVENTS_DAILY_TO_ARTIFACT, {
    variables: {
      artifactIds: stringToIntArray(props.ids),
      typeIds: props.eventTypes?.map((n) => EVENT_TYPE_NAME_TO_ID[n]),
      startDate: eventTimeToLabel(props.startDate ?? DEFAULT_START_DATE),
      endDate: eventTimeToLabel(props.endDate),
    },
  });
  const {
    data: artifactData,
    error: artifactError,
    loading: artifactLoading,
  } = useQuery(GET_ARTIFACTS_BY_IDS, {
    variables: { artifactIds: stringToIntArray(props.ids) },
  });
  const normalizedEventData: EventData[] = (
    rawEventData?.events_daily_to_artifact ?? []
  ).map((x) => ({
    typeId: ensure<number>(x.typeId, "Data missing 'typeId'"),
    id: ensure<number>(x.artifactId, "Data missing 'projectId'"),
    date: ensure<string>(x.bucketDaily, "Data missing 'bucketDaily'"),
    amount: ensure<number>(x.amount, "Data missing 'number'"),
  }));
  const formattedData = formatData(
    props,
    normalizedEventData,
    artifactData?.artifact,
  );
  console.log(props.ids, rawEventData, formattedData);
  return (
    <DataProviderView
      {...props}
      formattedData={formattedData}
      loading={eventLoading || artifactLoading}
      error={eventError ?? artifactError}
    />
  );
}

/**
 * EventDataProvider for projects
 * @param props
 * @returns
 */
function ProjectEventDataProvider(props: EventDataProviderProps) {
  const {
    data: rawEventData,
    error: eventError,
    loading: eventLoading,
  } = useQuery(GET_EVENTS_DAILY_TO_PROJECT, {
    variables: {
      projectIds: stringToIntArray(props.ids),
      typeIds: props.eventTypes?.map((n) => EVENT_TYPE_NAME_TO_ID[n]),
      startDate: eventTimeToLabel(props.startDate ?? DEFAULT_START_DATE),
      endDate: eventTimeToLabel(props.endDate),
    },
  });
  const {
    data: projectData,
    error: projectError,
    loading: projectLoading,
  } = useQuery(GET_PROJECTS_BY_IDS, {
    variables: { projectIds: stringToIntArray(props.ids) },
  });
  const normalizedData: EventData[] = (
    rawEventData?.events_daily_to_project ?? []
  ).map((x) => ({
    typeId: ensure<number>(x.typeId, "Data missing 'type'"),
    id: ensure<number>(x.projectId, "Data missing 'projectId'"),
    date: ensure<string>(x.bucketDaily, "Data missing 'bucketDaily'"),
    amount: ensure<number>(x.amount, "Data missing 'number'"),
  }));
  const formattedData = formatData(props, normalizedData, projectData?.project);
  console.log(props.ids, rawEventData, formattedData);
  return (
    <DataProviderView
      {...props}
      formattedData={formattedData}
      loading={eventLoading || projectLoading}
      error={eventError ?? projectError}
    />
  );
}

/**
 * Switches between the EventDataProvider implementation
 * depending on the `entityType`
 * @param props
 * @returns
 */
function EventDataProvider(props: EventDataProviderProps) {
  return props.entityType === "project" ? (
    <ProjectEventDataProvider {...props} />
  ) : (
    <ArtifactEventDataProvider {...props} />
  );
}

export {
  EventDataProvider,
  ProjectEventDataProvider,
  ArtifactEventDataProvider,
};
export type { EventDataProviderProps };
