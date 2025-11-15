import {
  type FilterMap,
  type QueryPredicate,
  type StringKeys,
  type TableRow,
  type ValidTableName,
} from "@/app/api/v1/osograph/utils/query-builder";

type FieldComparisonOperators<
  T extends ValidTableName,
  K extends StringKeys<TableRow<T>>,
> = {
  eq?: FilterMap<T>[K];
  neq?: FilterMap<T>[K];
  gt?: FilterMap<T>[K];
  gte?: FilterMap<T>[K];
  lt?: FilterMap<T>[K];
  lte?: FilterMap<T>[K];
  in?: Array<FilterMap<T>[K]>;
  like?: string;
  ilike?: string;
  is?: null | boolean;
};

export type WhereClause<T extends ValidTableName> = {
  [K in StringKeys<TableRow<T>>]?: FieldComparisonOperators<T, K>;
};

export function parseWhereClause<T extends ValidTableName>(
  where: WhereClause<T>,
): Partial<QueryPredicate<T>> {
  const predicate: Partial<QueryPredicate<T>> = {};

  for (const fieldKey in where) {
    const field = fieldKey as StringKeys<TableRow<T>>;
    const operators = where[field];

    if (!operators) continue;

    for (const operatorKey in operators) {
      const value =
        operators[
          operatorKey as keyof FieldComparisonOperators<T, typeof field>
        ];

      if (value === undefined) continue;

      const operator = operatorKey as keyof QueryPredicate<T>;

      if (!predicate[operator]) {
        predicate[operator] = [];
      }

      // @ts-expect-error - TS can't correlate the operator key with its corresponding filter entry type
      predicate[operator].push({ key: field, value });
    }
  }

  return predicate;
}
