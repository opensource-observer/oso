import { createAdminClient } from "@/lib/supabase/admin";
import type { GraphQLResolverMap } from "@apollo/subgraph/dist/schema-helper/resolverMap";
import {
  getUserProfile,
  requireAuthentication,
  type GraphQLContext,
} from "@/app/api/v1/osograph/utils/auth";
import { UserErrors, ServerErrors } from "@/app/api/v1/osograph/utils/errors";

export const userResolvers: GraphQLResolverMap<GraphQLContext> = {
  Query: {
    osoApp_me: async (_: unknown, _args: unknown, context: GraphQLContext) => {
      const authenticatedUser = requireAuthentication(context.user);
      return getUserProfile(authenticatedUser.userId);
    },
  },

  Mutation: {
    osoApp_updateMyProfile: async (
      _: unknown,
      args: { input: { fullName?: string; avatarUrl?: string } },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const { input } = args;

      const supabase = createAdminClient();

      const updateData: { full_name?: string; avatar_url?: string } = {};
      if (input.fullName !== undefined) {
        updateData.full_name = input.fullName;
      }
      if (input.avatarUrl !== undefined) {
        updateData.avatar_url = input.avatarUrl;
      }

      if (Object.keys(updateData).length === 0) {
        throw UserErrors.noFieldsToUpdate();
      }

      const { data: user, error } = await supabase
        .from("user_profiles")
        .update(updateData)
        .eq("id", authenticatedUser.userId)
        .select()
        .single();

      if (error) {
        throw ServerErrors.database(
          `Failed to update user profile: ${error.message}`,
        );
      }

      return {
        user,
        message: "Profile updated successfully",
        success: true,
      };
    },
  },

  User: {
    __resolveReference: async (reference: { id: string }) => {
      return getUserProfile(reference.id);
    },

    organizations: async (
      parent: { id: string },
      _args: unknown,
      _context: GraphQLContext,
    ) => {
      const supabase = createAdminClient();
      const { data: memberships } = await supabase
        .from("users_by_organization")
        .select("org_id, organizations(*)")
        .eq("user_id", parent.id)
        .is("deleted_at", null);

      if (!memberships) return [];

      return memberships
        .map((m) => m.organizations)
        .filter((org) => org !== null);
    },
  },
};
