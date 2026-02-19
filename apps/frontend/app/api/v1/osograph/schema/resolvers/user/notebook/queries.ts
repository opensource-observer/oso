import { getAuthenticatedClient } from "@/app/api/v1/osograph/utils/access-control";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { FilterableConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import {
  type ExplicitClientQueryOptions,
  queryWithPagination,
} from "@/app/api/v1/osograph/utils/query-helpers";
import { NotebookWhereSchema } from "@/app/api/v1/osograph/utils/validation";

export const notebookQueries: GraphQLResolverModule<GraphQLContext>["Query"] = {
  notebooks: async (
    _: unknown,
    args: FilterableConnectionArgs,
    context: GraphQLContext,
  ) => {
    const { client, orgIds } = await getAuthenticatedClient(context);

    const options: ExplicitClientQueryOptions<"notebooks"> = {
      client,
      orgIds,
      tableName: "notebooks",
      whereSchema: NotebookWhereSchema,
      basePredicate: {
        is: [{ key: "deleted_at", value: null }],
      },
    };

    return queryWithPagination(args, context, options);
  },
};
