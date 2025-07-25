import { SupabaseClient } from "@supabase/supabase-js";
import { HttpError } from "@opensource-observer/utils";

type SupabaseQueryArgs = {
  tableName: string; // table to query
  columns?: string; // comma-delimited column names (e.g. `address,claimId`)
  filters?: any; // A list of filters, where each filter is `[ column, operator, value ]`
  // See https://supabase.com/docs/reference/javascript/filter
  // e.g. [ [ "address", "eq", "0xabc123" ] ]
  limit?: number; // Number of results to return
  orderBy?: string; // Name of column to order by
  orderAscending?: boolean; // True if ascending, false if descending
};

async function supabaseQuery(
  supabaseClient: SupabaseClient,
  args: SupabaseQueryArgs,
): Promise<any[]> {
  const { tableName, columns, filters, limit, orderBy, orderAscending } = args;
  let query = supabaseClient.from(tableName as any).select(columns);
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
  // Limits
  if (limit) {
    query = query.limit(limit);
  }
  // Ordering
  if (orderBy) {
    query = query.order(orderBy, { ascending: orderAscending });
  }
  // Execute query
  const { data, error, status } = await query;
  if (error) {
    throw error;
  } else if (status > 300) {
    throw new HttpError(`Invalid status code: ${status}`);
  }

  return data;
}

export { supabaseQuery };
export type { SupabaseQueryArgs };
