import { getAuthenticatedClient } from "@/app/api/v1/osograph/utils/access-control";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { FilterableConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import { getUserOrganizationIds } from "@/app/api/v1/osograph/utils/resolver-helpers";
import {
  queryWithPagination,
  type ExplicitClientQueryOptions,
} from "@/app/api/v1/osograph/utils/query-helpers";
import { DataConnectionWhereSchema } from "@/app/api/v1/osograph/utils/validation";

export const dataConnectionQueries: GraphQLResolverModule<GraphQLContext>["Query"] =
  {
    dataConnections: async (
      _: unknown,
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      const { client, userId } = getAuthenticatedClient(context);
      const orgIds = await getUserOrganizationIds(userId, client);

      const options: ExplicitClientQueryOptions<"dynamic_connectors"> = {
        client,
        orgIds,
        tableName: "dynamic_connectors",
        whereSchema: DataConnectionWhereSchema,
        basePredicate: {
          is: [{ key: "deleted_at", value: null }],
        },
      };

      return queryWithPagination(args, context, options);
    },
  };
