import { getAuthenticatedClient } from "@/app/api/v1/osograph/utils/access-control";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { UserErrors } from "@/app/api/v1/osograph/utils/errors";
import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";

export const viewerQueries: GraphQLResolverModule<GraphQLContext>["Query"] = {
  viewer: async (_: unknown, _args: unknown, context: GraphQLContext) => {
    const { client, userId } = await getAuthenticatedClient(context);

    const { data: profile, error } = await client
      .from("user_profiles")
      .select("*")
      .eq("id", userId)
      .single();

    if (error || !profile) {
      throw UserErrors.profileNotFound();
    }

    return profile;
  },
};
