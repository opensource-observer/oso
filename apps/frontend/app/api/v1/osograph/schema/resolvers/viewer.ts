import { createAdminClient } from "@/lib/supabase/admin";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { requireAuthentication } from "@/app/api/v1/osograph/utils/auth";
import { UserErrors } from "@/app/api/v1/osograph/utils/errors";
import type { ConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import {
  getUserOrganizationsConnection,
  getUserInvitationsConnection,
  getUserOrganizationIds,
} from "@/app/api/v1/osograph/utils/resolver-helpers";
import { getNotebooksConnection } from "@/app/api/v1/osograph/schema/resolvers/notebook";
import { getDatasetsConnection } from "@/app/api/v1/osograph/schema/resolvers/dataset";

export const viewerResolvers: GraphQLResolverModule<GraphQLContext> = {
  Query: {
    viewer: async (_: unknown, _args: unknown, context: GraphQLContext) => {
      const authenticatedUser = requireAuthentication(context.user);
      const supabase = createAdminClient();

      const { data: profile, error } = await supabase
        .from("user_profiles")
        .select("*")
        .eq("id", authenticatedUser.userId)
        .single();

      if (error || !profile) {
        throw UserErrors.profileNotFound();
      }

      return profile;
    },
  },

  Viewer: {
    fullName: (parent: { full_name: string | null }) => parent.full_name,
    avatarUrl: (parent: { avatar_url: string | null }) => parent.avatar_url,

    organizations: async (
      parent: { id: string },
      args: ConnectionArgs,
      _context: GraphQLContext,
    ) => {
      return getUserOrganizationsConnection(parent.id, args);
    },

    notebooks: async (
      parent: { id: string },
      args: ConnectionArgs,
      _context: GraphQLContext,
    ) => {
      const orgIds = await getUserOrganizationIds(parent.id);
      return getNotebooksConnection(orgIds, args);
    },

    datasets: async (
      parent: { id: string },
      args: ConnectionArgs,
      _context: GraphQLContext,
    ) => {
      const orgIds = await getUserOrganizationIds(parent.id);
      return getDatasetsConnection(orgIds, args);
    },

    invitations: async (
      parent: { id: string; email: string },
      args: ConnectionArgs,
      _context: GraphQLContext,
    ) => {
      return getUserInvitationsConnection(parent.email, args);
    },
  },
};
