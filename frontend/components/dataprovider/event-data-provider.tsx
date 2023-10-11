import { DataProvider } from "@plasmicapp/loader-nextjs";
import dayjs from "dayjs";
import _ from "lodash";
import React, { ReactNode } from "react";
import { useQuery } from "@apollo/experimental-nextjs-app-support/ssr";
import { GET_EVENTS_DAILY_BY_ARTIFACT } from "../../lib/graphql/queries";
import { assertNever } from "../../lib/common";

// The name used to pass data into the Plasmic DataProvider
const DEFAULT_VARIABLE_NAME = "eventData";

type EventData = Partial<{
  toId: number;
  amount: any;
  bucketDaily: any;
  type: any;
}>;

const eventToValue = (e: EventData) => Math.max(e.amount, 1);

const formatDataToKpiCard = (data?: EventData[]) => {
  if (!data) {
    return { data: 0 };
  }
  const result = _.sumBy(data, eventToValue);
  return {
    data: result,
  };
};

const formatDataToAreaChart = (data?: EventData[]) => {
  if (!data) {
    return {
      data: [],
      categories: [],
      xAxis: "date",
    };
  }
  // Store the categories for the Tremor area chart
  const categories = new Set<string>();
  const simpleDates = data.map((x: EventData) => ({
    ...x,
    // Pull out the date
    date: dayjs(x.bucketDaily).format("YYYY-MM-DD"),
    // Get the value we want to plot
    value: eventToValue(x),
  }));
  //console.log(simpleDates);
  const groupedByDate = _.groupBy(simpleDates, (x) => x.date);
  //console.log(groupedByDate);

  // Sum the values for each (artifactId, eventType, date)
  const summed = _.mapValues(groupedByDate, (x) =>
    _.reduce(
      x,
      (accum, curr) => {
        const category = `${curr.toId} ${_.capitalize(
          curr.type.replace(/_/g, " "),
        )}`;
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

const formatDataToBarList = (xAxis: XAxis, data?: EventData[]) => {
  if (!data) {
    return { data: [] };
  }
  const grouped = _.groupBy(data, (x) =>
    xAxis === "eventTime"
      ? dayjs(x.bucketDaily).format("YYYY-MM-DD")
      : xAxis === "artifact"
      ? x.toId
      : xAxis === "eventType"
      ? x.type
      : assertNever(xAxis),
  );
  const summed = _.mapValues(grouped, (x) => _.sumBy(x, eventToValue));
  const result = _.toPairs(summed).map((x) => ({
    name: x[0],
    value: x[1],
  }));
  return {
    data: result,
  };
};

type ChartType = "kpiCard" | "areaChart" | "barList";
type XAxis = "eventTime" | "artifact" | "eventType";
type EntityType = "collection" | "project" | "artifact";

/**
 * Query component focused on providing data to visualiation components
 *
 * Current limitations:
 * - Does not support authentication or RLS. Make sure data is readable by unauthenticated users
 */
export type EventDataProviderProps = {
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

export function EventDataProvider(props: EventDataProviderProps) {
  // These props are set in the Plasmic Studio
  const {
    className,
    variableName,
    children,
    loadingChildren,
    ignoreLoading,
    errorChildren,
    ignoreError,
    useTestData,
    testData,
    chartType,
    xAxis,
    ids,
    eventTypes,
    startDate,
    endDate,
  } = props;
  const startDateObj = dayjs(startDate ?? 0);
  const endDateObj = endDate ? dayjs(endDate) : dayjs();
  const key = variableName ?? DEFAULT_VARIABLE_NAME;
  const {
    data: rawData,
    error,
    loading,
  } = useQuery(GET_EVENTS_DAILY_BY_ARTIFACT, {
    variables: {
      ids:
        ids?.map((id) => parseInt(id)).filter((id) => !!id && !isNaN(id)) ?? [],
      types: eventTypes ?? [],
      startDate: startDateObj.format("YYYY-MM-DD"),
      endDate: endDateObj.format("YYYY-MM-DD"),
    },
  });

  // Show when loading or error
  if (loading && !ignoreLoading && !!loadingChildren) {
    return <div className={className}> {loadingChildren} </div>;
  } else if (error && !ignoreError && !!errorChildren) {
    return (
      <div className={className}>
        <DataProvider name={key} data={error}>
          {errorChildren}
        </DataProvider>
      </div>
    );
  }

  //const checkedData = rawData as unknown as EventData[];
  // Short-circuit if test data
  const data = useTestData ? testData : rawData?.events_daily_by_artifact;
  const formattedData =
    chartType === "kpiCard"
      ? formatDataToKpiCard(data)
      : chartType === "areaChart"
      ? formatDataToAreaChart(data)
      : chartType === "barList"
      ? formatDataToBarList(xAxis ?? "artifact", data)
      : assertNever(chartType);

  return (
    <div className={className}>
      <DataProvider name={key} data={formattedData}>
        {children}
      </DataProvider>
    </div>
  );
}
