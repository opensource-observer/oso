import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import {
  ExplicitClientQueryOptions,
  queryWithPagination,
} from "@/app/api/v1/osograph/utils/query-helpers";
import { FilterableConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import { DataModelWhereSchema } from "@/app/api/v1/osograph/utils/validation";
import { getAuthenticatedClient } from "@/app/api/v1/osograph/utils/access-control";

export const dataModelQueries: GraphQLResolverModule<GraphQLContext>["Query"] =
  {
    dataModels: async (
      _: unknown,
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      const { client, orgIds } = await getAuthenticatedClient(context);

      const options: ExplicitClientQueryOptions<"model"> = {
        client,
        orgIds,
        tableName: "model",
        whereSchema: DataModelWhereSchema,
        basePredicate: {
          is: [{ key: "deleted_at", value: null }],
        },
      };

      return queryWithPagination(args, context, options);
    },
  };
