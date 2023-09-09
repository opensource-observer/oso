import { DataProvider } from "@plasmicapp/loader-nextjs";
import dayjs from "dayjs";
import _ from "lodash";
import React, { ReactNode } from "react";
import useSWRImmutable from "swr/immutable";
import { supabase } from "../../lib/supabase-client";
import { HttpError, MissingDataError } from "../../lib/errors";
import { assertNever } from "../../lib/common";

// The name used to pass data into the Plasmic DataProvider
const DEFAULT_VARIABLE_NAME = "eventData";
const KEY_PREFIX = "event";
const genKey = (props: EventDataProviderProps) => {
  let key = `${KEY_PREFIX}`;
  if (props.artifactIds) {
    key += `:${JSON.stringify(props.artifactIds)}`;
  }
  if (props.eventTypes) {
    key += `:${JSON.stringify(props.eventTypes)}`;
  }
  if (props.startDate) {
    key += `:${dayjs(props.startDate).format("YYYY-MM-DD")}`;
  }
  if (props.endDate) {
    key += `:${dayjs(props.endDate).format("YYYY-MM-DD")}`;
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

const formatDataToKpiCard = (data?: SupabaseEvent[]) => {
  if (!data) {
    return { data: 0 };
  }
  const result = _.sumBy(data, eventToValue);
  return {
    data: result,
  };
};

const formatDataToAreaChart = (data?: SupabaseEvent[]) => {
  if (!data) {
    return {
      data: [],
      categories: [],
      xAxis: "date",
    };
  }
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

const formatDataToBarList = (xAxis: XAxis, data?: SupabaseEvent[]) => {
  if (!data) {
    return { data: [] };
  }
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
  const startDateObj = dayjs(startDate ?? 0);
  const endDateObj = endDate ? dayjs(endDate) : dayjs();
  const key = variableName ?? DEFAULT_VARIABLE_NAME;
  const { data, error, isLoading } = useSWRImmutable(
    genKey(props),
    async () => {
      if (useTestData) {
        return testData;
      } else if (
        !artifactIds ||
        !Array.isArray(artifactIds) ||
        artifactIds.length <= 0
      ) {
        return null;
      } else if (
        !eventTypes ||
        !Array.isArray(eventTypes) ||
        eventTypes.length <= 0
      ) {
        return null;
      } else if (endDateObj.isBefore(startDateObj)) {
        return null;
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
        .gte("eventTime", startDateObj.format("YYYY-MM-DD"))
        .lte("eventTime", endDateObj.format("YYYY-MM-DD"))
        .limit(10000);

      if (error) {
        throw error;
      } else if (status > 300) {
        throw new HttpError(`Invalid status code: ${status}`);
      } else if (!rawData) {
        throw new MissingDataError("Missing data");
      }
      console.log("Supabase Events", rawData);
      return rawData;
    },
  );
  //const checkedData = rawData as unknown as SupabaseEvent[];
  const formattedData =
    chartType === "kpiCard"
      ? formatDataToKpiCard(data)
      : chartType === "areaChart"
      ? formatDataToAreaChart(data)
      : chartType === "barList"
      ? formatDataToBarList(xAxis ?? "artifact", data)
      : assertNever(chartType);

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
        <DataProvider name={key} data={formattedData}>
          {children}
        </DataProvider>
      </div>
    );
  }
}
