import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import {
  ExplicitClientQueryOptions,
  queryWithPagination,
} from "@/app/api/v1/osograph/utils/query-helpers";
import { FilterableConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import { StaticModelWhereSchema } from "@/app/api/v1/osograph/utils/validation";
import { getAuthenticatedClient } from "@/app/api/v1/osograph/utils/access-control";
import { getUserOrganizationIds } from "@/app/api/v1/osograph/utils/resolver-helpers";

export const staticModelQueries: GraphQLResolverModule<GraphQLContext>["Query"] =
  {
    staticModels: async (
      _: unknown,
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      const { client, userId } = getAuthenticatedClient(context);
      const orgIds = await getUserOrganizationIds(userId, client);

      const options: ExplicitClientQueryOptions<"static_model"> = {
        client,
        orgIds,
        tableName: "static_model",
        whereSchema: StaticModelWhereSchema,
        basePredicate: {
          is: [{ key: "deleted_at", value: null }],
        },
      };

      return queryWithPagination(args, context, options);
    },
  };
