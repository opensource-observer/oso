import React, { ReactNode } from "react";
import useSWR from "swr";
import { DataProvider } from "@plasmicapp/loader-nextjs";
import { supabase } from "../../lib/supabase-client";

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
export interface SupabaseQueryProps {
  className?: string; // Plasmic CSS class
  variableName?: string; // Name to use in Plasmic data picker
  children?: ReactNode; // Show this
  loadingChildren?: ReactNode; // Show during loading if !ignoreLoading
  ignoreLoading?: boolean; // Skip the loading visual
  errorChildren?: ReactNode; // Show if we get an error
  ignoreError?: boolean; // Skip the error visual
  tableName?: string; // table to query
  columns?: string; // comma-delimited column names (e.g. `address,claimId`)
  filters?: any; // A list of filters, where each filter is `[ column, operator, value ]`
  // See https://supabase.com/docs/reference/javascript/filter
  // e.g. [ [ "address", "eq", "0xabc123" ] ]
  limit?: number; // Number of results to return
  orderBy?: string; // Name of column to order by
  orderAscending?: boolean; // True if ascending, false if descending
  useTestData?: boolean;
  testData?: any;
}

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
    columns,
    filters,
    limit,
    orderBy,
    orderAscending,
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
    let query = supabase.from(tableName).select(columns);
    // Iterate over the filters
    if (Array.isArray(filters)) {
      for (let i = 0; i < filters.length; i++) {
        const f = filters[i];
        if (!Array.isArray(f) || f.length < 3) {
          console.warn(`Invalid supabase filter: ${f}`);
          continue;
        }
        query = query.filter(f[0], f[1], f[2]);
      }
    }
    if (limit) {
      query = query.limit(limit);
    }
    if (orderBy) {
      query = query.order(orderBy, { ascending: orderAscending });
    }
    // Execute query
    const { data, error, status } = await query;
    if (error && status !== 406) {
      throw error;
    } else {
      return data;
    }
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
