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

export type TableWithOrgId = Extract<
  ValidTableName,
  {
    [K in ValidTableName]: "org_id" extends keyof TableRow<K> ? K : never;
  }[ValidTableName]
>;

interface BaseQueryOptions<TTable extends TableWithOrgId> {
  tableName: TTable;
  whereSchema: z.ZodSchema;
  errorMessage?: string;
  basePredicate?: Partial<QueryPredicate<TTable>>;
}

export type QueryConnectionOptions<TTable extends TableWithOrgId> =
  | (BaseQueryOptions<TTable> & {
      filterByUserOrgs: true;
      requireAuth: true;
    })
  | (BaseQueryOptions<TTable> & {
      filterByUserOrgs: false;
      requireAuth: boolean;
      parentOrgIds: string | string[];
    });

async function resolveOrgIds<TTable extends TableWithOrgId>(
  options: QueryConnectionOptions<TTable>,
  context: GraphQLContext,
): Promise<string[]> {
  if (options.filterByUserOrgs) {
    const authenticatedUser = requireAuthentication(context.user);
    return await getUserOrganizationIds(authenticatedUser.userId);
  }

  if (options.requireAuth) {
    requireAuthentication(context.user);
  }

  return Array.isArray(options.parentOrgIds)
    ? options.parentOrgIds
    : [options.parentOrgIds];
}

export async function queryWithPagination<TTable extends TableWithOrgId>(
  args: FilterableConnectionArgs,
  context: GraphQLContext,
  options: QueryConnectionOptions<TTable>,
) {
  const supabase = createAdminClient();

  const orgIds = await resolveOrgIds(options, context);
  if (orgIds.length === 0) {
    return emptyConnection<TableRow<TTable>>();
  }

  const [start, end] = preparePaginationRange(args);

  const orgIdPredicate: Partial<QueryPredicate<TTable>> = {
    // @ts-expect-error - TS can't correlate that org_id exists on all TableWithOrgId tables
    in: [{ key: "org_id", value: orgIds }],
  };

  const basePredicate = options.basePredicate
    ? mergePredicates(orgIdPredicate, options.basePredicate)
    : orgIdPredicate;

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
    args.single,
  );

  if (error) {
    const errorMessage =
      options.errorMessage ||
      `Failed to fetch ${options.tableName}: ${error.message}`;
    throw ServerErrors.database(errorMessage);
  }

  return buildConnectionOrEmpty(data, args, count);
}
