import { DataProvider } from "@plasmicapp/loader-nextjs";
import React, { ReactNode } from "react";
import useSWR from "swr";
import { supabase } from "../../lib/supabase-client";
import { HttpError } from "../../lib/errors";

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

type ChartType = "kpiCard" | "areaChart" | "barList";
type XAxis = "date" | "artifact" | "eventType";

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
  } = props;
  const key = variableName ?? genKey(props);
  const { data, error, isLoading } = useSWR(key, async () => {
    if (useTestData) {
      return testData;
    }

    const { data, error, status } = await supabase
      .from("Event")
      .select()
      .limit(1);
    //const startDateObj = new Date(startDate ?? 0);
    //const endDateObj = endDate ? new Date(endDate) : new Date();
    //.in("project.github_org", githubOrgs ?? [])
    //.in("event_type", eventTypes ?? []);
    //.select(
    //  "id, project:project_id!inner(id, github_org), event_type, timestamp, amount, details",
    //)
    //.gte("timestamp", startDateObj.toISOString())
    //.lte("timestamp", endDateObj.toISOString());

    if (error) {
      throw error;
    } else if (status > 300) {
      throw new HttpError(`Invalid status code: ${status}`);
    } else if (!data) {
      throw new Error("Missing data");
    }
    console.log(data);
    return data;

    /**
    const simpleDates = data.map((x: any) => ({
      date: dayjs(x.timestamp).format("YYYY-MM-DD"),
      amount: x.amount,
    }));
    console.log(simpleDates);
    const grouped = _.groupBy(simpleDates, (x) => x.date);
    console.log(grouped);
    const summed = _.mapValues(grouped, (x) =>
      _.sum(x.map((y) => y.amount)),
    );
    console.log(summed);
    const unsorted = _.toPairs(summed).map((x) => ({
      date: x[0],
      value: x[1],
    }));
    const result = _.sortBy(unsorted, (x) => x.date);
    console.log(result);
    return result;
    */
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
