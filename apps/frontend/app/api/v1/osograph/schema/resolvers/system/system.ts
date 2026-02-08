import { getSystemClient } from "@/app/api/v1/osograph/utils/access-control";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";

export const systemQueries: GraphQLResolverModule<GraphQLContext>["Query"] = {
  system: async (_: unknown, _args: unknown, context: GraphQLContext) => {
    // System-level operations require valid systemCredentials.
    // Access control is enforced by getSystemClient() validation.
    const _client = getSystemClient(context);
    return {};
  },
};
