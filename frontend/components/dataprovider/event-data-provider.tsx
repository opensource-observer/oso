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

// The name used to pass data into the Plasmic DataProvider
const DEFAULT_VARIABLE_NAME = "eventData";

type EventData = {
  type: string;
  id: number;
  date: string;
  amount: number;
};

const eventTimeToLabel = (t: any) => dayjs(t).format("YYYY-MM-DD");
const eventTypeToLabel = (t: string) => _.capitalize(t.replace(/_/g, " "));

const formatDataToKpiCard = (data: EventData[]) => {
  const result = _.sumBy(data, (x) => x.amount);
  return {
    data: result,
  };
};

const formatDataToAreaChart = (data: EventData[]) => {
  // Store the categories for the Tremor area chart
  const categories = new Set<string>();
  const simpleDates = data.map((x: EventData) => ({
    ...x,
    // Pull out the date
    date: eventTimeToLabel(x.date),
    // Get the value we want to plot
    value: x.amount,
  }));
  //console.log(simpleDates);
  const groupedByDate = _.groupBy(simpleDates, (x) => x.date);
  //console.log(groupedByDate);

  // Sum the values for each (artifactId, eventType, date)
  const summed = _.mapValues(groupedByDate, (x) =>
    _.reduce(
      x,
      (accum, curr) => {
        //const category = `${curr.toId} ${eventTypeToLabel(curr.type)}`;
        const category = `${eventTypeToLabel(curr.type)}`;
        categories.add(category);
        return {
          ...accum,
          [category]: (accum[category] ?? 0) + curr.value,
        };
      },
      {} as Record<string, number>,
    ),
  );
  // Flatten into an array
  //console.log(summed);
  const unsorted = _.toPairs(summed).map((x) => ({
    ...x[1],
    date: x[0],
  }));
  // Sort by date
  const result = _.sortBy(unsorted, (x) => x.date);
  //console.log(result);
  return {
    data: result,
    categories: Array.from(categories),
    xAxis: "date",
  };
};

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

type ChartType = "kpiCard" | "areaChart" | "barList";
type XAxis = "eventTime" | "artifact" | "eventType";
type EntityType = "project" | "artifact";

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

const createVariables = (props: EventDataProviderProps) => ({
  ids:
    props.ids?.map((id) => parseInt(id)).filter((id) => !!id && !isNaN(id)) ??
    [],
  types: props.eventTypes ?? [],
  startDate: eventTimeToLabel(props.startDate ?? 0),
  endDate: eventTimeToLabel(props.endDate),
});

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
      ? formatDataToAreaChart(data)
      : props.chartType === "barList"
      ? formatDataToBarList(props.xAxis ?? "artifact", data)
      : assertNever(props.chartType);
  return formattedData;
};

function ArtifactEventDataProvider(props: EventDataProviderProps) {
  // These props are set in the Plasmic Studio
  const key = props.variableName ?? DEFAULT_VARIABLE_NAME;
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

  // Show when loading or error
  if (loading && !props.ignoreLoading && !!props.loadingChildren) {
    return <div className={props.className}> {props.loadingChildren} </div>;
  } else if (error && !props.ignoreError && !!props.errorChildren) {
    return (
      <div className={props.className}>
        <DataProvider name={key} data={error}>
          {props.errorChildren}
        </DataProvider>
      </div>
    );
  }
  return (
    <div className={props.className}>
      <DataProvider name={key} data={formattedData}>
        {props.children}
      </DataProvider>
    </div>
  );
}

function ProjectEventDataProvider(props: EventDataProviderProps) {
  // These props are set in the Plasmic Studio
  const key = props.variableName ?? DEFAULT_VARIABLE_NAME;
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

  // Show when loading or error
  if (loading && !props.ignoreLoading && !!props.loadingChildren) {
    return <div className={props.className}> {props.loadingChildren} </div>;
  } else if (error && !props.ignoreError && !!props.errorChildren) {
    return (
      <div className={props.className}>
        <DataProvider name={key} data={error}>
          {props.errorChildren}
        </DataProvider>
      </div>
    );
  }
  return (
    <div className={props.className}>
      <DataProvider name={key} data={formattedData}>
        {props.children}
      </DataProvider>
    </div>
  );
}

function EventDataProvider(props: EventDataProviderProps) {
  return props.entityType === "project" ? (
    <ProjectEventDataProvider {...props} />
  ) : (
    <ArtifactEventDataProvider {...props} />
  );
}

export { EventDataProvider };
export type { EventDataProviderProps };
