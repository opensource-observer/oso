import { Database } from "@/lib/types/supabase";
import { createServerClient } from "@/lib/supabase/server";

type SupabaseClient = Awaited<ReturnType<typeof createServerClient>>;

export type ValidTableName = keyof Database["public"]["Tables"];

export type TableRow<T extends ValidTableName> =
  Database["public"]["Tables"][T]["Row"];

export type StringKeys<T> = Extract<keyof T, string>;

export type FilterMap<T extends ValidTableName> = {
  [K in StringKeys<TableRow<T>>]: TableRow<T>[K];
};

export type TypedFilterEntry<T extends ValidTableName, V> = {
  [K in StringKeys<TableRow<T>>]: { key: K; value: V };
}[StringKeys<TableRow<T>>];

export type FilterEntry<T extends ValidTableName> = TypedFilterEntry<
  T,
  FilterMap<T>[StringKeys<TableRow<T>>]
>;

export type ArrayFilterEntry<T extends ValidTableName> = TypedFilterEntry<
  T,
  Array<FilterMap<T>[StringKeys<TableRow<T>>]>
>;

export type StringFilterEntry<T extends ValidTableName> = TypedFilterEntry<
  T,
  string
>;

export type NullableFilterEntry<T extends ValidTableName> = TypedFilterEntry<
  T,
  null | boolean
>;

export type QueryPredicate<T extends ValidTableName> = {
  eq?: FilterEntry<T>[];
  neq?: FilterEntry<T>[];
  gt?: FilterEntry<T>[];
  gte?: FilterEntry<T>[];
  lt?: FilterEntry<T>[];
  lte?: FilterEntry<T>[];
  in?: ArrayFilterEntry<T>[];
  like?: StringFilterEntry<T>[];
  ilike?: StringFilterEntry<T>[];
  is?: NullableFilterEntry<T>[];
};

export function _inferQueryType<TTable extends ValidTableName>(
  client: SupabaseClient,
  tableName: TTable,
) {
  return client.from(tableName).select("*", { count: "exact" });
}

export async function buildQuery<TTable extends ValidTableName>(
  client: SupabaseClient,
  tableName: TTable,
  predicate: Partial<QueryPredicate<TTable>>,
  hook?: <TQuery extends ReturnType<typeof _inferQueryType<TTable>>>(
    query: TQuery,
  ) => TQuery,
) {
  type TQuery = ReturnType<typeof _inferQueryType<TTable>>;
  let query = client.from(tableName).select("*", { count: "exact" });

  function applyFilter<K extends StringKeys<TableRow<TTable>>>(
    q: TQuery,
    key: K,
    value: FilterMap<TTable>[K],
    method: "eq" | "neq" | "gt" | "gte" | "lt" | "lte",
  ): TQuery {
    // @ts-expect-error - TS can't correlate generic K with union method signatures
    return q[method](key, value);
  }

  function applyIn<K extends StringKeys<TableRow<TTable>>>(
    q: TQuery,
    key: K,
    value: Array<FilterMap<TTable>[K]>,
  ): TQuery {
    // @ts-expect-error - TS can't narrow FilterMap<TTable>[K][] to Supabase types
    return q.in(key, value);
  }

  function applyStringFilter<K extends StringKeys<TableRow<TTable>>>(
    q: TQuery,
    key: K,
    value: string,
    method: "like" | "ilike",
  ): TQuery {
    return q[method](key, value);
  }

  function applyIs<K extends StringKeys<TableRow<TTable>>>(
    q: TQuery,
    key: K,
    value: null | boolean,
  ): TQuery {
    return q.is(key, value);
  }

  const handlers: {
    [K in keyof QueryPredicate<TTable>]-?: (
      q: TQuery,
      filter: NonNullable<QueryPredicate<TTable>[K]>[number],
    ) => TQuery;
  } = {
    eq: (q, f) => applyFilter(q, f.key, f.value, "eq"),
    neq: (q, f) => applyFilter(q, f.key, f.value, "neq"),
    gt: (q, f) => applyFilter(q, f.key, f.value, "gt"),
    gte: (q, f) => applyFilter(q, f.key, f.value, "gte"),
    lt: (q, f) => applyFilter(q, f.key, f.value, "lt"),
    lte: (q, f) => applyFilter(q, f.key, f.value, "lte"),
    in: (q, f) => applyIn(q, f.key, f.value),
    like: (q, f) => applyStringFilter(q, f.key, f.value, "like"),
    ilike: (q, f) => applyStringFilter(q, f.key, f.value, "ilike"),
    is: (q, f) => applyIs(q, f.key, f.value),
  };

  for (const key of Object.keys(
    predicate,
  ) as (keyof QueryPredicate<TTable>)[]) {
    const filters = predicate[key];
    if (!filters) continue;

    const handler = handlers[key];
    for (const filter of filters) {
      if (filter.value !== undefined) {
        // @ts-expect-error - TS cannot correlate handler type with predicate key
        query = handler(query, filter);
      }
    }
  }

  return hook?.(query) ?? query;
}

export function mergePredicates<T extends ValidTableName>(
  ...predicates: Partial<QueryPredicate<T>>[]
): Partial<QueryPredicate<T>> {
  const merged: Partial<QueryPredicate<T>> = {};

  for (const predicate of predicates) {
    for (const [key, filters] of Object.entries(predicate)) {
      const operatorKey = key as keyof QueryPredicate<T>;
      if (!merged[operatorKey]) {
        merged[operatorKey] = [];
      }
      if (filters && Array.isArray(filters)) {
        // @ts-expect-error - TS can't correlate operator key with its filter entry array type
        merged[operatorKey].push(...filters);
      }
    }
  }

  return merged;
}
