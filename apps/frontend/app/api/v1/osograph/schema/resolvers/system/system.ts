import { getSystemClient } from "@/app/api/v1/osograph/utils/access-control";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import { queryWithPagination } from "@/app/api/v1/osograph/utils/query-helpers";
import { FilterableConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import { RunWhereSchema } from "@/app/api/v1/osograph/utils/validation";

export const systemQueries: GraphQLResolverModule<GraphQLContext>["Query"] = {
  system: async (_: unknown, _args: unknown, context: GraphQLContext) => {
    // TODO(jabolo): Check for perms manually here?
    const _client = getSystemClient(context);
    return {};
  },

  runs: async (
    _: unknown,
    args: FilterableConnectionArgs,
    context: GraphQLContext,
  ) => {
    // TODO(jabolo): How do we get user orgs from the system handler?
    // Is it everything? How do we do it now?

    // eslint-disable-next-line @typescript-eslint/no-deprecated
    return queryWithPagination(args, context, {
      tableName: "run",
      whereSchema: RunWhereSchema,
      requireAuth: true,
      filterByUserOrgs: true,
    });
  },
};
