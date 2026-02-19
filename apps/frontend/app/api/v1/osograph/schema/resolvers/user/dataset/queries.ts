import {
  getAuthenticatedClient,
  RESOURCE_CONFIG,
} from "@/app/api/v1/osograph/utils/access-control";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { FilterableConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import {
  getFetchLimit,
  getPaginationParams,
} from "@/app/api/v1/osograph/utils/pagination";
import { buildConnectionOrEmpty } from "@/app/api/v1/osograph/utils/resolver-helpers";
import { emptyConnection } from "@/app/api/v1/osograph/utils/connection";
import {
  queryWithPagination,
  type ExplicitClientQueryOptions,
} from "@/app/api/v1/osograph/utils/query-helpers";
import { DatasetWhereSchema } from "@/app/api/v1/osograph/utils/validation";
import {
  OrganizationErrors,
  ServerErrors,
} from "@/app/api/v1/osograph/utils/errors";
import type {
  QueryMarketplaceDatasetsArgs,
  DatasetType,
} from "@/lib/graphql/generated/graphql";
import { logger } from "@/lib/logger";

export const datasetQueries: GraphQLResolverModule<GraphQLContext>["Query"] = {
  datasets: async (
    _: unknown,
    args: FilterableConnectionArgs,
    context: GraphQLContext,
  ) => {
    const { client, orgIds } = await getAuthenticatedClient(context);

    const options: ExplicitClientQueryOptions<"datasets"> = {
      client,
      orgIds,
      tableName: "datasets",
      whereSchema: DatasetWhereSchema,
      basePredicate: {
        is: [
          { key: "deleted_at", value: null },
          { key: "permission.revoked_at", value: null },
        ],
        in: [{ key: "permission.org_id", value: orgIds }],
      },
      resourceConfig: RESOURCE_CONFIG["dataset"],
    };

    return queryWithPagination(args, context, options);
  },

  marketplaceDatasets: async (
    _: unknown,
    args: QueryMarketplaceDatasetsArgs,
    context: GraphQLContext,
  ) => {
    const { client, orgIds } = await getAuthenticatedClient(context);

    if (!orgIds.includes(args.orgId)) {
      logger.warn(
        `Org ${args.orgId} attempted to access marketplace datasets, but is not part of the requesting orgs.`,
      );
      return OrganizationErrors.notFound();
    }

    // 1. Get public dataset IDs from resource_permissions
    const { data: publicPerms, error: permsError } = await client
      .from("resource_permissions")
      .select("dataset_id")
      .not("dataset_id", "is", null)
      .is("user_id", null)
      .is("org_id", null)
      .is("revoked_at", null);

    if (permsError) {
      logger.error("Failed to fetch public dataset permissions:", permsError);
      throw ServerErrors.internal("Failed to fetch public datasets");
    }

    const publicDatasetIds = (publicPerms ?? [])
      .map((p) => p.dataset_id)
      .filter((id): id is string => id !== null);

    if (publicDatasetIds.length === 0) {
      return emptyConnection();
    }

    // 2. Build query - join organizations for search and to avoid N+1
    const connectionArgs = {
      first: args.first ?? 25,
      after: args.after ?? undefined,
    };
    const { offset } = getPaginationParams(connectionArgs);
    const fetchLimit = getFetchLimit(connectionArgs);

    let query = client
      .from("datasets")
      .select("*, test:organizations!inner(org_name), filter:organizations()", {
        count: "exact",
      })
      .in("id", publicDatasetIds)
      .not("org_id", "eq", args.orgId) // Exclude datasets owned by the org
      .is("deleted_at", null);

    // Search across dataset name, display_name, and organization name
    if (args.search) {
      query = query
        .or(
          `name.ilike.%${args.search}%,display_name.ilike.%${args.search}%,filter.not.is.null`,
        )
        .ilike("filter.org_name", `%${args.search}%`);
    }

    if (args.datasetType) {
      query = query.eq("dataset_type", args.datasetType as DatasetType);
    }

    // 3. Apply pagination and ordering
    query = query
      .order("created_at", { ascending: false })
      .range(offset, offset + fetchLimit - 1);

    const { data, count, error } = await query;

    if (error) {
      logger.error("Failed to fetch marketplace datasets:", error);
      throw ServerErrors.internal("Failed to fetch marketplace datasets");
    }

    return buildConnectionOrEmpty(data, connectionArgs, count);
  },
};
