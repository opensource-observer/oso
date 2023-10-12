import { DataProvider } from "@plasmicapp/loader-nextjs";
import dayjs from "dayjs";
import _ from "lodash";
import React, { ReactNode } from "react";
import { useQuery } from "@apollo/experimental-nextjs-app-support/ssr";
import {
  GET_EVENTS_DAILY_BY_ARTIFACT,
  GET_EVENTS_DAILY_BY_PROJECT,
} from "../../lib/graphql/queries";
import { assertNever, ensure, uncheckedCast } from "../../lib/common";
import { ApolloError } from "@apollo/client";

type ChartType = "kpiCard" | "areaChart" | "barList";
type XAxis = "eventTime" | "artifact" | "eventType";
type EntityType = "project" | "artifact";

// The name used to pass data into the Plasmic DataProvider
const DEFAULT_VARIABLE_NAME = "eventData";
// Default entity type if not specified
const DEFAULT_ENTITY_TYPE: EntityType = "artifact";
// Default XAxis if not specified
const DEFAULT_XAXIS: XAxis = "eventType";

/**
 * Regardless of the data query, this will be the intermediate
 * format we need to normalize against before we put it into the
 * data formatters (for charts)
 **/
type EventData = {
  type: string;
  id: number;
  date: string;
  amount: number;
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
 * Formats normalized data into inputs to a KPI card
 * @param data - normalized data
 * @returns
 */
const formatDataToKpiCard = (data: EventData[]) => {
  const result = _.sumBy(data, (x) => x.amount);
  return {
    data: result,
  };
};

/**
 * Formats normalized data into inputs to an area chart (for Tremor)
 * @param data
 * @returns
 */
const formatDataToAreaChart = (
  data: EventData[],
  categories: string[],
  entityType: EntityType,
) => {
  // Start with an empty data point for each date
  const emptyDataPoint = _.fromPairs(categories.map((c) => [c, 0]));
  const datesWithData = _.uniq(data.map((x) => eventTimeToLabel(x.date)));
  const groupedByDate = _.fromPairs(
    datesWithData.map((d) => [d, _.clone(emptyDataPoint)]),
  );
  //console.log(groupedByDate);

  // Sum the values for each (date, artifactId, eventType)
  data.forEach((d) => {
    const dateLabel = eventTimeToLabel(d.date);
    const category = createCategory(entityType, d.id, d.type);
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
    for (const cat of categories) {
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
  const sliced = result.slice(i, j + 1);

  return {
    data: sliced,
    categories,
    xAxis: "date",
  };
};

/**
 * Formats normalized data for a bar chart (for Tremor)
 * @param xAxis
 * @param data
 * @returns
 */
const formatDataToBarList = (xAxis: XAxis, data: EventData[]) => {
  const grouped = _.groupBy(data, (x) =>
    xAxis === "eventTime"
      ? x.date
      : xAxis === "artifact"
      ? x.id
      : xAxis === "eventType"
      ? x.type
      : assertNever(xAxis),
  );
  const summed = _.mapValues(grouped, (x) => _.sumBy(x, (x) => x.amount));
  const result = _.toPairs(summed).map((x) => ({
    name:
      xAxis === "eventTime"
        ? eventTimeToLabel(x[0])
        : xAxis === "artifact"
        ? x[0]
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
 * Query component focused on providing data to visualiation components
 *
 * Current limitations:
 * - Does not support authentication or RLS. Make sure data is readable by unauthenticated users
 */
type EventDataProviderProps = {
  className?: string; // Plasmic CSS class
  variableName?: string; // Name to use in Plasmic data picker
  children?: ReactNode; // Show this
  loadingChildren?: ReactNode; // Show during loading if !ignoreLoading
  ignoreLoading?: boolean; // Skip the loading visual
  errorChildren?: ReactNode; // Show if error
  ignoreError?: boolean; // Skip the error visual
  useTestData?: boolean; // Use the testData prop instead of querying database
  testData?: any;
  chartType: ChartType;
  xAxis?: XAxis; // X-axis
  entityType?: EntityType;
  ids?: string[];
  eventTypes?: string[];
  startDate?: string;
  endDate?: string;
};

/**
 * Create the variables object for the GraphQL query
 * @param props
 * @returns
 */
const createVariables = (props: EventDataProviderProps) => ({
  ids:
    props.ids?.map((id) => parseInt(id)).filter((id) => !!id && !isNaN(id)) ??
    [],
  types: props.eventTypes ?? [],
  startDate: eventTimeToLabel(props.startDate ?? 0),
  endDate: eventTimeToLabel(props.endDate),
});

/**
 * TODO: Creates unique categories for the area chart
 * - Currently, we just use the type, which will merge data across IDs
 * - We need to add unique identifiers for each ID to properly segregate
 * @param entityType
 * @param id
 * @param type
 * @returns
 */
const createCategory = (entityType: EntityType, id: number, type: string) =>
  `${eventTypeToLabel(type)}`;

const createCategories = (props: EventDataProviderProps) => {
  const entityType = props.entityType ?? DEFAULT_ENTITY_TYPE;
  const ids = (props.ids ?? [])
    .map(parseInt)
    .filter((id) => !!id && !isNaN(id));
  const types = props.eventTypes ?? [];
  const result: string[] = [];
  for (const id of ids) {
    for (const type of types) {
      result.push(createCategory(entityType, id, type));
    }
  }
  return result;
};

/**
 * Switches on the props to return formatted data
 * @param props - component props
 * @param rawData - normalized data from a GraphQL query
 * @returns
 */
const formatData = (props: EventDataProviderProps, rawData: EventData[]) => {
  //const checkedData = rawData as unknown as EventData[];
  // Short-circuit if test data
  const data = props.useTestData
    ? uncheckedCast<EventData[]>(props.testData)
    : rawData;

  const formattedData =
    props.chartType === "kpiCard"
      ? formatDataToKpiCard(data)
      : props.chartType === "areaChart"
      ? formatDataToAreaChart(
          data,
          createCategories(props),
          props.entityType ?? DEFAULT_ENTITY_TYPE,
        )
      : props.chartType === "barList"
      ? formatDataToBarList(props.xAxis ?? DEFAULT_XAXIS, data)
      : assertNever(props.chartType);
  return formattedData;
};

type ProviderViewProps = EventDataProviderProps & {
  formattedData: any;
  loading: boolean;
  error?: ApolloError;
};

/**
 * Common view logic for EventDataProviders
 * @param props
 * @returns
 */
function ProviderView(props: ProviderViewProps) {
  const key = props.variableName ?? DEFAULT_VARIABLE_NAME;
  // Show when loading or error
  if (props.loading && !props.ignoreLoading && !!props.loadingChildren) {
    return <div className={props.className}> {props.loadingChildren} </div>;
  } else if (props.error && !props.ignoreError && !!props.errorChildren) {
    return (
      <div className={props.className}>
        <DataProvider name={key} data={props.error}>
          {props.errorChildren}
        </DataProvider>
      </div>
    );
  }
  return (
    <div className={props.className}>
      <DataProvider name={key} data={props.formattedData}>
        {props.children}
      </DataProvider>
    </div>
  );
}

/**
 * EventDataProvider for artifacts
 * @param props
 * @returns
 */
function ArtifactEventDataProvider(props: EventDataProviderProps) {
  const variables = createVariables(props);
  const {
    data: rawData,
    error,
    loading,
  } = useQuery(GET_EVENTS_DAILY_BY_ARTIFACT, { variables });
  const normalizedData: EventData[] = (
    rawData?.events_daily_by_artifact ?? []
  ).map((x) => ({
    type: ensure<string>(x.type, "Data missing 'type'"),
    id: ensure<number>(x.toId, "Data missing 'projectId'"),
    date: ensure<string>(x.bucketDaily, "Data missing 'bucketDaily'"),
    amount: ensure<number>(x.amount, "Data missing 'number'"),
  }));
  const formattedData = formatData(props, normalizedData);
  console.log(props.ids, rawData, formattedData);
  return (
    <ProviderView
      {...props}
      formattedData={formattedData}
      loading={loading}
      error={error}
    />
  );
}

/**
 * EventDataProvider for projects
 * @param props
 * @returns
 */
function ProjectEventDataProvider(props: EventDataProviderProps) {
  const variables = createVariables(props);
  const {
    data: rawData,
    error,
    loading,
  } = useQuery(GET_EVENTS_DAILY_BY_PROJECT, { variables });
  const normalizedData: EventData[] = (
    rawData?.events_daily_by_project ?? []
  ).map((x) => ({
    type: ensure<string>(x.type, "Data missing 'type'"),
    id: ensure<number>(x.projectId, "Data missing 'projectId'"),
    date: ensure<string>(x.bucketDaily, "Data missing 'bucketDaily'"),
    amount: ensure<number>(x.amount, "Data missing 'number'"),
  }));
  const formattedData = formatData(props, normalizedData);
  console.log(props.ids, rawData, formattedData);
  return (
    <ProviderView
      {...props}
      formattedData={formattedData}
      loading={loading}
      error={error}
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

export { EventDataProvider };
export type { EventDataProviderProps };
