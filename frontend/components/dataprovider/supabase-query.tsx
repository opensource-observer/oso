import React, { ReactNode } from "react";
import useSWR from "swr";
import { DataProvider } from "@plasmicapp/loader-nextjs";
import { SupabaseQueryArgs, supabaseQuery } from "../../lib/clients/supabase";

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
export type SupabaseQueryProps = Partial<SupabaseQueryArgs> & {
  className?: string; // Plasmic CSS class
  variableName?: string; // Name to use in Plasmic data picker
  children?: ReactNode; // Show this
  loadingChildren?: ReactNode; // Show during loading if !ignoreLoading
  ignoreLoading?: boolean; // Skip the loading visual
  errorChildren?: ReactNode; // Show if we get an error
  ignoreError?: boolean; // Skip the error visual
  useTestData?: boolean; // Use the testData prop instead of querying database
  testData?: any;
};

export function SupabaseQuery(props: SupabaseQueryProps) {
  // These props are set in the Plasmic Studio
  const {
    className,
    variableName,
    children,
    loadingChildren,
    ignoreLoading,
    errorChildren,
    ignoreError,
    tableName,
    useTestData,
    testData,
  } = props;
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
