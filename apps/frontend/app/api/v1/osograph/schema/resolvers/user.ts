import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import type { ConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import { getUserOrganizationsConnection } from "@/app/api/v1/osograph/utils/resolver-helpers";

export const userResolvers: GraphQLResolverModule<GraphQLContext> = {
  User: {
    fullName: (parent: { full_name: string | null }) => parent.full_name,
    avatarUrl: (parent: { avatar_url: string | null }) => parent.avatar_url,

    organizations: async (
      parent: { id: string },
      args: ConnectionArgs,
      _context: GraphQLContext,
    ) => {
      return getUserOrganizationsConnection(parent.id, args);
    },
  },
};
