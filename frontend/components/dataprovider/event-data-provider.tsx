import { DataProvider } from "@plasmicapp/loader-nextjs";
import dayjs from "dayjs";
import _ from "lodash";
import React, { ReactNode } from "react";
import useSWR from "swr";
import { supabase } from "../../lib/supabase-client";
import { HttpError, MissingDataError } from "../../lib/errors";
import { assertNever } from "../../lib/common";

// The name used to pass data into the Plasmic DataProvider
const KEY_PREFIX = "event";
const genKey = (props: EventDataProviderProps) => {
  let key = `${KEY_PREFIX}`;
  if (props.xAxis) {
    key += `:${props.xAxis}`;
  }
  if (props.artifactIds) {
    key += `:${JSON.stringify(props.artifactIds)}`;
  }
  if (props.eventTypes) {
    key += `:${JSON.stringify(props.eventTypes)}`;
  }
  if (props.startDate) {
    key += `:${props.startDate}`;
  }
  if (props.endDate) {
    key += `:${props.endDate}`;
  }
  return key;
};

type SupabaseEvent = {
  id: number;
  artifact: {
    id: number;
    type: string;
    namespace: string;
    name: string;
  };
  eventType: string;
  eventTime: string;
  amount: number;
};

const eventToValue = (e: SupabaseEvent) => Math.max(e.amount, 1);

const formatDataToKpiCard = (data: SupabaseEvent[]) => {
  const result = _.sumBy(data, eventToValue);
  return {
    data: result,
  };
};

const formatDataToAreaChart = (data: SupabaseEvent[]) => {
  // Store the categories for the Tremor area chart
  const categories = new Set<string>();
  const simpleDates = data.map((x: SupabaseEvent) => ({
    ...x,
    // Pull out the date
    date: dayjs(x.eventTime).format("YYYY-MM-DD"),
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
        const category = `${curr.artifact.name} ${_.capitalize(
          curr.eventType.replace(/_/g, " "),
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

const formatDataToBarList = (data: SupabaseEvent[], xAxis: XAxis) => {
  const grouped = _.groupBy(data, (x) =>
    xAxis === "eventTime"
      ? dayjs(x.eventTime).format("YYYY-MM-DD")
      : xAxis === "artifact"
      ? x.artifact.name
      : xAxis === "eventType"
      ? x.eventType
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
  artifactIds?: string[];
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
    artifactIds,
    eventTypes,
    startDate,
    endDate,
  } = props;
  const startDateObj = new Date(startDate ?? 0);
  const endDateObj = endDate ? new Date(endDate) : new Date();
  const key = variableName ?? genKey(props);
  const { data, error, isLoading } = useSWR(key, async () => {
    if (useTestData) {
      return testData;
    }

    const {
      data: rawData,
      error,
      status,
    } = await supabase
      .from("Event")
      .select(
        "id, artifact:artifactId!inner(id, type, namespace, name), eventType, eventTime, amount",
      )
      .in("artifactId", artifactIds ?? [])
      .in("eventType", eventTypes ?? [])
      .gte("eventTime", startDateObj.toISOString())
      .lte("eventTime", endDateObj.toISOString())
      .limit(10000);

    if (error) {
      throw error;
    } else if (status > 300) {
      throw new HttpError(`Invalid status code: ${status}`);
    } else if (!rawData) {
      throw new MissingDataError("Missing data");
    }
    console.log("Supabase Events", rawData);
    const checkedData = rawData as unknown as SupabaseEvent[];
    if (chartType === "kpiCard") {
      return formatDataToKpiCard(checkedData);
    } else if (chartType === "areaChart") {
      return formatDataToAreaChart(checkedData);
    } else if (chartType === "barList") {
      return formatDataToBarList(checkedData, xAxis ?? "artifact");
    } else {
      assertNever(chartType);
    }
  });

  // Show when loading
  if (isLoading && !ignoreLoading && !!loadingChildren) {
    return <div className={className}> {loadingChildren} </div>;
  } else if (error && !ignoreError && !!errorChildren) {
    return (
      <div className={className}>
        <DataProvider name={key} data={error}>
          {errorChildren}
        </DataProvider>
      </div>
    );
  } else {
    return (
      <div className={className}>
        <DataProvider name={key} data={data}>
          {children}
        </DataProvider>
      </div>
    );
  }
}
