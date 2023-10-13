import React from "react";
import useSWR from "swr";
import { SupabaseQueryArgs, supabaseQuery } from "../../lib/clients/supabase";
import { CommonDataProviderProps, DataProviderView } from "./provider-view";

// The name used to pass data into the Plasmic DataProvider
const KEY_PREFIX = "db";
const genKey = (props: SupabaseQueryProps) => {
  let key = `${KEY_PREFIX}:${props.tableName}`;
  if (props.columns) {
    key += `:${props.columns}`;
  }
  if (props.filters) {
    key += `:${JSON.stringify(props.filters)}`;
  }
  if (props.limit) {
    key += `:${props.limit}`;
  }
  if (props.orderBy) {
    key += `:${props.orderBy}`;
  }
  if (props.orderAscending) {
    key += `:${props.orderAscending}`;
  }
  return key;
};

/**
 * Generic Supabase query component.
 *
 * Current limitations:
 * - Does not support authentication or RLS. Make sure data is readable by unauthenticated users
 */
export type SupabaseQueryProps = Partial<SupabaseQueryArgs> &
  CommonDataProviderProps;

export function SupabaseQuery(props: SupabaseQueryProps) {
  // These props are set in the Plasmic Studio
  const { variableName, tableName, useTestData, testData } = props;
  const key = variableName ?? genKey(props);
  const { data, error, isLoading } = useSWR(key, async () => {
    if (useTestData) {
      return testData;
    } else if (!tableName) {
      return;
    }
    return await supabaseQuery({ ...props, tableName });
  });

  // Error messages are currently rendered in the component
  if (!tableName) {
    return <p>You need to set the tableName prop</p>;
  }

  return (
    <DataProviderView
      {...props}
      formattedData={data}
      loading={isLoading}
      error={error}
    />
  );
}
