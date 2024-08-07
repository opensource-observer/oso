import { useQuery } from "@apollo/client";
import dayjs from "dayjs";
import _ from "lodash";
import React from "react";
import {
  assertNever,
  safeCast,
  ensure,
  uncheckedCast,
} from "@opensource-observer/utils";
import {
  GET_ARTIFACTS_BY_IDS,
  GET_PROJECTS_BY_IDS,
  GET_COLLECTIONS_BY_IDS,
  GET_TIMESERIES_METRICS_BY_ARTIFACT,
  GET_TIMESERIES_METRICS_BY_PROJECT,
  GET_TIMESERIES_METRICS_BY_COLLECTION,
} from "../../lib/graphql/queries";
import {
  entityIdToLabel,
  eventTimeToLabel,
  eventTypeToLabel,
} from "../../lib/parsing";
import { RegistrationProps } from "../../lib/types/plasmic";
import type { EntityData, EventData } from "../../lib/types/db";
import {
  DataProviderView,
  CommonDataProviderRegistration,
} from "./provider-view";
import type { CommonDataProviderProps } from "./provider-view";
import { useEnsureAuth } from "./apollo-wrapper";

// Types used in the Plasmic registration
type ChartType = "areaChart" | "barList";
type XAxis = "date" | "entity" | "metric";
type EntityType = "artifact" | "project" | "collection";

// Ideal minimum number of data points in an area chart
type BucketWidth = "day" | "week" | "month";
const MIN_DATA_POINTS = 20;
// Default start time
const DEFAULT_START_DATE = 0;
// Default XAxis if not specified
const DEFAULT_XAXIS: XAxis = "date";

/**
 * Generic query component focused on providing metrics data to visualiation components
 */
type MetricsDataProviderProps = CommonDataProviderProps & {
  chartType: ChartType;
  xAxis?: XAxis; // X-axis
  entityType: EntityType;
  entityIds?: string[];
  metricIds?: string[];
  startDate?: string;
  endDate?: string;
};

/**
 * Plasmic component registration
 */
const MetricsDataProviderRegistration: RegistrationProps<MetricsDataProviderProps> =
  {
    ...CommonDataProviderRegistration,
    chartType: {
      type: "choice",
      helpText: "Pair this with the component in 'children'",
      options: safeCast<ChartType[]>(["areaChart", "barList"]),
    },
    xAxis: {
      type: "choice",
      helpText: "What is the x-axis?",
      options: safeCast<XAxis[]>(["date", "entity", "metric"]),
    },
    entityType: {
      type: "choice",
      helpText: "What kind of entity?",
      options: safeCast<EntityType[]>(["artifact", "project", "collection"]),
    },
    entityIds: {
      type: "array",
      defaultValue: [],
    },
    metricIds: {
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
const getBucketWidth = (props: MetricsDataProviderProps): BucketWidth => {
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
  id: string,
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
  const ids = props.ids ?? [];
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
 * Generic MetricsDataProvider
 * @param props
 * @returns
 */
function MetricsDataProvider(props: MetricsDataProviderProps) {
  useEnsureAuth();
  const bucketWidth = getBucketWidth(props);
  const variables = {
    metricIds: props.metricIds ?? [],
    startDate: eventTimeToLabel(props.startDate ?? DEFAULT_START_DATE),
    endDate: eventTimeToLabel(props.endDate),
    ...(props.entityType === "artifact"
      ? { artifactIds: props.entityIds ?? [] }
      : {}),
    ...(props.entityType === "project"
      ? { projectIds: props.entityIds ?? [] }
      : {}),
    ...(props.entityType === "collection"
      ? { collectionIds: props.entityIds ?? [] }
      : {}),
  };
  const metricsQuery =
    props.entityType === "artifact"
      ? GET_TIMESERIES_METRICS_BY_ARTIFACT
      : props.entityType === "project"
        ? GET_TIMESERIES_METRICS_BY_PROJECT
        : props.entityType === "collection"
          ? GET_TIMESERIES_METRICS_BY_COLLECTION
          : assertNever(props.entityType);
  const {
    data: rawMetricsData,
    error: metricsError,
    loading: metricsLoading,
  } = useQuery(metricsQuery, { variables });
  const entityQuery =
    props.entityType === "artifact"
      ? GET_ARTIFACTS_BY_IDS
      : props.entityType === "project"
        ? GET_PROJECTS_BY_IDS
        : props.entityType === "collection"
          ? GET_COLLECTIONS_BY_IDS
          : assertNever(props.entityType);
  const {
    data: entitiesData,
    error: entitiesError,
    loading: entitiesLoading,
  } = useQuery(entityQuery, { variables });
  const normalizedData: EventData[] = (
    (rawMetricsData as any)?.events_monthly_to_collection ??
    (rawMetricsData as any)?.events_weekly_to_collection ??
    rawMetricsData?.events_daily_to_collection ??
    []
  ).map((x: any) => ({
    typeName: ensure<string>(x.event_type, "Data missing 'event_type'"),
    id: ensure<string>(x.collection_id, "Data missing 'collection_id'"),
    date: ensure<string>(
      x.bucket_day ?? x.bucket_week ?? x.bucket_month,
      "Data missing time",
    ),
    amount: ensure<number>(x.amount, "Data missing 'number'"),
  }));
  const entityData = entitiesData?.collections_v1.map((x) => ({
    id: ensure<string>(x.collection_id, "collection missing 'collection_id'"),
    name: ensure<string>(
      x.collection_name,
      "collection missing 'collection_name'",
    ),
  }));
  const formattedData = formatData(props, normalizedData, entityData, {
    gapFill: bucketWidth === "day",
  });
  !metricsLoading &&
    console.log(props, rawMetricsData, metricsError, formattedData);
  return (
    <DataProviderView
      {...props}
      formattedData={formattedData}
      loading={metricsLoading || entitiesLoading}
      error={metricsError ?? entitiesError}
    />
  );
}

export { MetricsDataProviderRegistration, MetricsDataProvider };
export type { MetricsDataProviderProps };
