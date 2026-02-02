import {
  createAdminClient,
  type SupabaseAdminClient,
} from "@/lib/supabase/admin";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { requireAuthentication } from "@/app/api/v1/osograph/utils/auth";
import { ServerErrors } from "@/app/api/v1/osograph/utils/errors";
import {
  type ConnectionArgs,
  type FilterableConnectionArgs,
  getFetchLimit,
  getPaginationParams,
} from "@/app/api/v1/osograph/utils/pagination";
import {
  buildConnectionOrEmpty,
  getUserOrganizationIds,
} from "@/app/api/v1/osograph/utils/resolver-helpers";
import {
  type Connection,
  emptyConnection,
} from "@/app/api/v1/osograph/utils/connection";
import { validateInput } from "@/app/api/v1/osograph/utils/validation";
import {
  buildQuery,
  mergePredicates,
  OrderBy,
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
  orderBy?: OrderBy<TTable>;
}

export interface ExplicitClientQueryOptions<TTable extends TableWithOrgId>
  extends BaseQueryOptions<TTable> {
  client: SupabaseAdminClient;
  orgIds: string | string[];
}

/**
 * @deprecated Use ExplicitClientQueryOptions with explicit client parameter.
 */
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

function isExplicitClientOptions<TTable extends TableWithOrgId>(
  options: ExplicitClientQueryOptions<TTable> | QueryConnectionOptions<TTable>,
): options is ExplicitClientQueryOptions<TTable> {
  return "client" in options && "orgIds" in options;
}

/**
 * @deprecated
 */
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

async function queryWithExplicitClient<TTable extends TableWithOrgId>(
  args: FilterableConnectionArgs,
  context: GraphQLContext,
  options: ExplicitClientQueryOptions<TTable>,
) {
  const supabase = options.client;
  let orgIdPredicate: Partial<QueryPredicate<TTable>> = {};

  if (!context.systemCredentials) {
    const normalizedOrgIds = Array.isArray(options.orgIds)
      ? options.orgIds
      : [options.orgIds];

    if (normalizedOrgIds.length === 0) {
      return emptyConnection<TableRow<TTable>>();
    }

    orgIdPredicate = {
      // @ts-expect-error - TS can't correlate that org_id exists on all TableWithOrgId tables
      in: [{ key: "org_id", value: normalizedOrgIds }],
    };
  }

  const orderBy = options.orderBy;
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
    (query) => {
      query = orderBy
        ? query.order(orderBy.key, {
            ascending: orderBy.ascending ?? false,
          })
        : query;
      return maybeAddQueryPagination(query, args);
    },
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

async function queryWithImplicitClient<TTable extends TableWithOrgId>(
  args: FilterableConnectionArgs,
  context: GraphQLContext,
  options: QueryConnectionOptions<TTable>,
) {
  const supabase = createAdminClient();

  let orgIdPredicate: Partial<QueryPredicate<TTable>> = {};

  if (!context.systemCredentials) {
    const orgIds = await resolveOrgIds(options, context);
    if (orgIds.length === 0) {
      return emptyConnection<TableRow<TTable>>();
    }

    orgIdPredicate = {
      // @ts-expect-error - TS can't correlate that org_id exists on all TableWithOrgId tables
      in: [{ key: "org_id", value: orgIds }],
    };
  }

  const orderBy = options.orderBy;

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
    (query) => {
      query = orderBy
        ? query.order(orderBy.key, {
            ascending: orderBy.ascending ?? false,
          })
        : query;
      return maybeAddQueryPagination(query, args);
    },
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

export async function queryWithPagination<TTable extends TableWithOrgId>(
  args: FilterableConnectionArgs,
  context: GraphQLContext,
  options: ExplicitClientQueryOptions<TTable>,
): Promise<Connection<TableRow<TTable>>>;

/**
 * @deprecated
 */
export async function queryWithPagination<TTable extends TableWithOrgId>(
  args: FilterableConnectionArgs,
  context: GraphQLContext,
  options: QueryConnectionOptions<TTable>,
): Promise<Connection<TableRow<TTable>>>;

export async function queryWithPagination<TTable extends TableWithOrgId>(
  args: FilterableConnectionArgs,
  context: GraphQLContext,
  options: ExplicitClientQueryOptions<TTable> | QueryConnectionOptions<TTable>,
) {
  if (isExplicitClientOptions(options)) {
    return queryWithExplicitClient(args, context, options);
  }

  return queryWithImplicitClient(args, context, options);
}

/**
 * Prepares the pagination range [start, end] based on the provided ConnectionArgs.
 * @param args - The connection arguments containing pagination info. If first is 0, no pagination is needed.
 * @returns the range as a tuple [start, end], or undefined if no pagination is needed.
 */
function preparePaginationRange(
  args: ConnectionArgs,
): [number, number] | undefined {
  const { limit: first, offset } = getPaginationParams(args);
  if (first === 0) {
    return undefined;
  }
  const limit = getFetchLimit(args);
  return [offset, offset + limit - 1];
}

export function maybeAddQueryPagination<
  TQuery extends { range: (from: number, to: number) => TQuery },
>(query: TQuery, args: FilterableConnectionArgs) {
  const pagination = preparePaginationRange(args);
  if (pagination) {
    query = query.range(pagination[0], pagination[1]);
  }
  return query;
}
