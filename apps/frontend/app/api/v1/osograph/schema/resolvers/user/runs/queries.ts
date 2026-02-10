import { getAuthenticatedClient } from "@/app/api/v1/osograph/utils/access-control";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import { queryWithPagination } from "@/app/api/v1/osograph/utils/query-helpers";
import { FilterableConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import { RunWhereSchema } from "@/app/api/v1/osograph/utils/validation";
import { getUserOrganizationIds } from "@/app/api/v1/osograph/utils/resolver-helpers";

/**
 * Top-level runs query that fetches runs for the authenticated user's organizations.
 */
export const runsQueries: GraphQLResolverModule<GraphQLContext>["Query"] = {
  runs: async (
    _: unknown,
    args: FilterableConnectionArgs,
    context: GraphQLContext,
  ) => {
    const { client, userId } = getAuthenticatedClient(context);
    const orgIds = await getUserOrganizationIds(userId, client);

    return queryWithPagination(args, context, {
      client,
      orgIds,
      tableName: "run",
      whereSchema: RunWhereSchema,
    });
  },
};
