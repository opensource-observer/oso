import { createAdminClient } from "@/lib/supabase/admin";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { requireAuthentication } from "@/app/api/v1/osograph/utils/auth";
import { ServerErrors } from "@/app/api/v1/osograph/utils/errors";
import type { FilterableConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import {
  buildConnectionOrEmpty,
  getUserOrganizationIds,
  preparePaginationRange,
} from "@/app/api/v1/osograph/utils/resolver-helpers";
import { emptyConnection } from "@/app/api/v1/osograph/utils/connection";
import { validateInput } from "@/app/api/v1/osograph/utils/validation";
import {
  buildQuery,
  mergePredicates,
  type QueryPredicate,
  type TableRow,
  type ValidTableName,
} from "@/app/api/v1/osograph/utils/query-builder";
import { parseWhereClause } from "@/app/api/v1/osograph/utils/where-parser";
import type { z } from "zod";

type OrgIdsContext<TKey extends string> = {
  [K in TKey]: string[];
};

type PredicateBuilder<TTable extends ValidTableName, TKey extends string> = (
  context: OrgIdsContext<TKey>,
) => Partial<QueryPredicate<TTable>>;

interface BaseQueryOptions<TTable extends ValidTableName> {
  tableName: TTable;
  whereSchema: z.ZodSchema;
  errorMessage?: string;
}

export type QueryConnectionOptions<TTable extends ValidTableName> =
  | (BaseQueryOptions<TTable> & {
      filterByUserOrgs: true;
      requireAuth: true;
      buildBasePredicate: PredicateBuilder<TTable, "userOrgIds">;
    })
  | (BaseQueryOptions<TTable> & {
      filterByUserOrgs: false;
      requireAuth: boolean;
      parentOrgIds: string | string[];
      buildBasePredicate: PredicateBuilder<TTable, "parentOrgIds">;
    });

export async function queryWithPagination<TTable extends ValidTableName>(
  args: FilterableConnectionArgs,
  context: GraphQLContext,
  options: QueryConnectionOptions<TTable>,
) {
  const supabase = createAdminClient();

  let orgIds: string[];
  if (options.filterByUserOrgs) {
    const authenticatedUser = requireAuthentication(context.user);
    orgIds = await getUserOrganizationIds(authenticatedUser.userId);
    if (orgIds.length === 0) {
      return emptyConnection<TableRow<TTable>>();
    }
  } else {
    if (options.requireAuth) {
      requireAuthentication(context.user);
    }
    orgIds = Array.isArray(options.parentOrgIds)
      ? options.parentOrgIds
      : [options.parentOrgIds];
  }

  const [start, end] = preparePaginationRange(args);

  const basePredicate = options.filterByUserOrgs
    ? options.buildBasePredicate({ userOrgIds: orgIds })
    : options.buildBasePredicate({ parentOrgIds: orgIds });

  const validatedWhere = args.where
    ? validateInput(options.whereSchema, args.where)
    : undefined;

  const predicate = validatedWhere
    ? mergePredicates(basePredicate, parseWhereClause(validatedWhere))
    : basePredicate;

  const { data, count, error } = await buildQuery(
    supabase,
    options.tableName,
    predicate,
    (query) => query.range(start, end),
  );

  if (error) {
    const errorMessage =
      options.errorMessage ||
      `Failed to fetch ${options.tableName}: ${error.message}`;
    throw ServerErrors.database(errorMessage);
  }

  return buildConnectionOrEmpty(data, args, count);
}
