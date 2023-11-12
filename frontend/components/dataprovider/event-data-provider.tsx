import { useQuery } from "@apollo/experimental-nextjs-app-support/ssr";
import dayjs from "dayjs";
import _ from "lodash";
import React from "react";
import { assertNever, ensure, uncheckedCast } from "../../lib/common";
import {
  GET_ALL_EVENT_TYPES,
  GET_ARTIFACTS_BY_IDS,
  GET_EVENTS_DAILY_TO_ARTIFACT,
  GET_EVENTS_WEEKLY_TO_ARTIFACT,
  GET_EVENTS_MONTHLY_TO_ARTIFACT,
  GET_EVENTS_DAILY_TO_PROJECT,
  GET_EVENTS_WEEKLY_TO_PROJECT,
  GET_EVENTS_MONTHLY_TO_PROJECT,
  GET_USERS_MONTHLY_TO_PROJECT,
  GET_PROJECTS_BY_IDS,
  GET_EVENTS_MONTHLY_TO_COLLECTION,
  GET_EVENTS_WEEKLY_TO_COLLECTION,
  GET_EVENTS_DAILY_TO_COLLECTION,
  GET_COLLECTIONS_BY_IDS,
} from "../../lib/graphql/queries";
import {
  entityIdToLabel,
  eventTimeToLabel,
  eventTypeToLabel,
  stringToIntArray,
} from "../../lib/parsing";
import { RegistrationProps } from "../../lib/types/plasmic";
import type { EntityData, EventData } from "../../lib/types/db";
import {
  DataProviderView,
  CommonDataProviderRegistration,
} from "./provider-view";
import type { CommonDataProviderProps } from "./provider-view";

// Types used in the Plasmic registration
type BucketWidth = "day" | "week" | "month";
type ChartType = "areaChart" | "barList";
type XAxis = "eventTime" | "entity" | "eventType";

// Ideal minimum number of data points in an area chart
const MIN_DATA_POINTS = 20;
// Default start time
const DEFAULT_START_DATE = 0;
// Default XAxis if not specified
const DEFAULT_XAXIS: XAxis = "eventType";

/**
 * Query component focused on providing data to visualiation components
 *
 * Current limitations:
 * - Does not support authentication or RLS. Make sure data is readable by unauthenticated users
 */
type EventDataProviderProps = CommonDataProviderProps & {
  chartType: ChartType;
  xAxis?: XAxis; // X-axis
  ids?: string[];
  eventTypes?: string[];
  startDate?: string;
  endDate?: string;
};

/**
 * Plasmic component registration
 */
const EventDataProviderRegistration: RegistrationProps<EventDataProviderProps> =
  {
    ...CommonDataProviderRegistration,
    chartType: {
      type: "choice",
      helpText: "Pair this with the component in 'children'",
      options: ["areaChart", "barList"],
    },
    xAxis: {
      type: "choice",
      helpText: "What is the x-axis?",
      options: ["eventTime", "entity", "eventType"],
    },
    ids: {
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
 * Choose a bucket width based on the number of data points
 */
const getBucketWidth = (props: EventDataProviderProps): BucketWidth => {
  const startDate = dayjs(props.startDate ?? DEFAULT_START_DATE);
  const endDate = dayjs(props.endDate);
  if (endDate.diff(startDate, "month") > MIN_DATA_POINTS) {
    return "month";
  } else if (endDate.diff(startDate, "week") > MIN_DATA_POINTS) {
    return "week";
  } else {
    return "day";
  }
};

/**
 * EventType from GraphQL
 */
type EventType = {
  id: number;
  name: string;
};

/**
 * Converts an event type from id to name
 * @param id
 * @param eventTypes
 * @returns
 */
const eventTypeIdToName = (id: number, eventTypes: EventType[]) => {
  const map = _.fromPairs(eventTypes.map((t) => [t.id, t.name]));
  return map[id];
};

/**
 * Converts an event type from name to id
 * @param name
 * @param eventTypes
 * @returns
 */
const eventTypeNameToId = (name: string, eventTypes: EventType[]) => {
  const map = _.fromPairs(eventTypes.map((t) => [t.name, t.id]));
  return map[name];
};

/**
 * Used in formatting chart data
 */
type FormatOpts = {
  // Should we fill in empty dates with 0's?
  gapFill?: boolean;
};

/**
 * Formats normalized data into inputs to an area chart (for Tremor)
 * @param data
 * @returns
 */
const formatDataToAreaChart = (
  data: EventData[],
  categories: { results: string[]; opts: CategoryOpts },
  entityData?: EntityData[],
  formatOpts?: FormatOpts,
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
      d.typeName,
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
  const sorted = _.sortBy(unsorted, (x) => x.date);
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
  let [i, j] = [0, sorted.length - 1];
  while (i < sorted.length && isEmptyDataPoint(sorted[i])) {
    i++;
  }
  while (j > 0 && isEmptyDataPoint(sorted[j])) {
    j--;
  }
  // TODO: we are only trimming the right side to see if users like this better.
  //const sliced = sorted.slice(i, j + 1);
  const sliced = sorted.slice(0, j + 1);
  //categories.results.includes("Downloads") && console.log(sliced);

  // Fill in any empty dates
  let filled;
  if (formatOpts?.gapFill) {
    let currDate = dayjs(sliced[0]?.date);
    filled = [];
    for (const x of sliced) {
      const thisDate = dayjs(x.date);
      while (currDate.isBefore(thisDate)) {
        filled.push({
          ...emptyDataPoint,
          date: currDate.format("YYYY-MM-DD"),
        });
        currDate = currDate.add(1, "day");
      }
      filled.push(x);
      currDate = thisDate.add(1, "day");
    }
    //categories.results.includes("Downloads") && console.log(filled);
  } else {
    filled = sliced;
  }

  return {
    data: filled,
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
      ? x.typeName
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

type CategoryOpts = {
  includeIds?: boolean;
  includeTypes?: boolean;
};

/**
 * Creates unique categories for the area chart
 * @param id
 * @param type
 * @param entityData
 * @param opts
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

/**
 * Create all categories
 */
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
  formatOpts?: FormatOpts,
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
          formatOpts,
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
  const bucketWidth = getBucketWidth(props);
  const {
    data: eventTypeData,
    error: eventTypeError,
    loading: eventTypeLoading,
  } = useQuery(GET_ALL_EVENT_TYPES);
  const eventTypes = eventTypeData?.event_type ?? [];
  const query =
    bucketWidth === "month"
      ? GET_EVENTS_MONTHLY_TO_ARTIFACT
      : bucketWidth === "week"
      ? GET_EVENTS_WEEKLY_TO_ARTIFACT
      : GET_EVENTS_DAILY_TO_ARTIFACT;
  const {
    data: rawEventData,
    error: eventError,
    loading: eventLoading,
  } = useQuery(query, {
    variables: {
      artifactIds: stringToIntArray(props.ids),
      typeIds: props.eventTypes?.map((n) => eventTypeNameToId(n, eventTypes)),
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
    (rawEventData as any)?.events_monthly_to_artifact ??
    (rawEventData as any)?.events_weekly_to_artifact ??
    rawEventData?.events_daily_to_artifact ??
    []
  ).map((x: any) => ({
    typeName: ensure<string>(
      eventTypeIdToName(x.typeId, eventTypes),
      "Data missing 'typeId'",
    ),
    id: ensure<number>(x.artifactId, "Data missing 'projectId'"),
    date: ensure<string>(
      x.bucketDaily ?? x.bucketWeekly ?? x.bucketMonthly,
      "Data missing time",
    ),
    amount: ensure<number>(x.amount, "Data missing 'number'"),
  }));
  const formattedData = formatData(
    props,
    normalizedEventData,
    artifactData?.artifact,
    { gapFill: bucketWidth === "day" },
  );
  console.log(props.ids, rawEventData, formattedData);
  return (
    <DataProviderView
      {...props}
      formattedData={formattedData}
      loading={eventTypeLoading || eventLoading || artifactLoading}
      error={eventTypeError ?? eventError ?? artifactError}
    />
  );
}

/**
 * EventDataProvider for projects
 * @param props
 * @returns
 */
function ProjectEventDataProvider(props: EventDataProviderProps) {
  const bucketWidth = getBucketWidth(props);
  const {
    data: eventTypeData,
    error: eventTypeError,
    loading: eventTypeLoading,
  } = useQuery(GET_ALL_EVENT_TYPES);
  const eventTypes = eventTypeData?.event_type ?? [];
  const query =
    bucketWidth === "month"
      ? GET_EVENTS_MONTHLY_TO_PROJECT
      : bucketWidth === "week"
      ? GET_EVENTS_WEEKLY_TO_PROJECT
      : GET_EVENTS_DAILY_TO_PROJECT;
  const {
    data: rawEventData,
    error: eventError,
    loading: eventLoading,
  } = useQuery(query, {
    variables: {
      projectIds: stringToIntArray(props.ids),
      typeIds: props.eventTypes?.map((n) => eventTypeNameToId(n, eventTypes)),
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
    (rawEventData as any)?.events_monthly_to_project ??
    (rawEventData as any)?.events_weekly_to_project ??
    rawEventData?.events_daily_to_project ??
    []
  ).map((x: any) => ({
    typeName: ensure<string>(
      eventTypeIdToName(x.typeId, eventTypes),
      "Data missing 'type'",
    ),
    id: ensure<number>(x.projectId, "Data missing 'projectId'"),
    date: ensure<string>(
      x.bucketDaily ?? x.bucketWeekly ?? x.bucketMonthly,
      "Data missing time",
    ),
    amount: ensure<number>(x.amount, "Data missing 'number'"),
  }));
  const formattedData = formatData(
    props,
    normalizedData,
    projectData?.project,
    { gapFill: bucketWidth === "day" },
  );
  console.log(props.ids, rawEventData, formattedData);
  return (
    <DataProviderView
      {...props}
      formattedData={formattedData}
      loading={eventTypeLoading || eventLoading || projectLoading}
      error={eventTypeError ?? eventError ?? projectError}
    />
  );
}

/**
 * EventDataProvider for collections
 * @param props
 * @returns
 */
function CollectionEventDataProvider(props: EventDataProviderProps) {
  const bucketWidth = getBucketWidth(props);
  const {
    data: eventTypeData,
    error: eventTypeError,
    loading: eventTypeLoading,
  } = useQuery(GET_ALL_EVENT_TYPES);
  const eventTypes = eventTypeData?.event_type ?? [];
  const query =
    bucketWidth === "month"
      ? GET_EVENTS_MONTHLY_TO_COLLECTION
      : bucketWidth === "week"
      ? GET_EVENTS_WEEKLY_TO_COLLECTION
      : GET_EVENTS_DAILY_TO_COLLECTION;
  const {
    data: rawEventData,
    error: eventError,
    loading: eventLoading,
  } = useQuery(query, {
    variables: {
      collectionIds: stringToIntArray(props.ids),
      typeIds: props.eventTypes?.map((n) => eventTypeNameToId(n, eventTypes)),
      startDate: eventTimeToLabel(props.startDate ?? DEFAULT_START_DATE),
      endDate: eventTimeToLabel(props.endDate),
    },
  });
  const {
    data: collectionData,
    error: collectionError,
    loading: collectionLoading,
  } = useQuery(GET_COLLECTIONS_BY_IDS, {
    variables: { collectionIds: stringToIntArray(props.ids) },
  });
  const normalizedData: EventData[] = (
    (rawEventData as any)?.events_monthly_to_collection ??
    (rawEventData as any)?.events_weekly_to_collection ??
    rawEventData?.events_daily_to_collection ??
    []
  ).map((x: any) => ({
    typeName: ensure<string>(
      eventTypeIdToName(x.typeId, eventTypes),
      "Data missing 'type'",
    ),
    id: ensure<number>(x.collectionId, "Data missing 'collectionId'"),
    date: ensure<string>(
      x.bucketDay ?? x.bucketWeekly ?? x.bucketMonthly,
      "Data missing time",
    ),
    amount: ensure<number>(x.amount, "Data missing 'number'"),
  }));
  const formattedData = formatData(
    props,
    normalizedData,
    collectionData?.collection,
    { gapFill: bucketWidth === "day" },
  );
  console.log(props.ids, rawEventData, formattedData);
  return (
    <DataProviderView
      {...props}
      formattedData={formattedData}
      loading={eventTypeLoading || eventLoading || collectionLoading}
      error={eventTypeError ?? eventError ?? collectionError}
    />
  );
}

/**
 * UserDataProvider for projects
 * @param props
 * @returns
 */
function ProjectUserDataProvider(props: EventDataProviderProps) {
  const {
    data: rawEventData,
    error: eventError,
    loading: eventLoading,
  } = useQuery(GET_USERS_MONTHLY_TO_PROJECT, {
    variables: {
      projectIds: stringToIntArray(props.ids),
      segmentTypes: props.eventTypes ?? [],
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
    rawEventData?.users_monthly_to_project ?? []
  ).map((x) => ({
    typeName: ensure<string>(x.segmentType, "Data missing 'segmentType'"),
    id: ensure<number>(x.projectId, "Data missing 'projectId'"),
    date: ensure<string>(x.bucketMonthly, "Data missing time"),
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

export {
  EventDataProviderRegistration,
  CollectionEventDataProvider,
  ProjectEventDataProvider,
  ArtifactEventDataProvider,
  ProjectUserDataProvider,
};
export type { EventDataProviderProps };
