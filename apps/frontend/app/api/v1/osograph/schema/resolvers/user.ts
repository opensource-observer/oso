import { createAdminClient } from "@/lib/supabase/admin";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { requireAuthentication } from "@/app/api/v1/osograph/utils/auth";
import { UserErrors, ServerErrors } from "@/app/api/v1/osograph/utils/errors";

export const userResolvers = {
  Query: {},

  Mutation: {
    updateMyProfile: async (
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
    email: (parent: { email: string }) => parent.email,
    fullName: (parent: { full_name: string | null }) => parent.full_name,
    avatarUrl: (parent: { avatar_url: string | null }) => parent.avatar_url,
    role: (parent: { role?: string }) => parent.role || "member",

    organizations: async (
      parent: { id: string },
      args: {
        limit?: number;
        offset?: number;
        where?: unknown;
        order_by?: unknown;
      },
      _context: GraphQLContext,
    ) => {
      const supabase = createAdminClient();
      const { data: memberships } = await supabase
        .from("users_by_organization")
        .select("org_id, organizations(*)")
        .eq("user_id", parent.id)
        .is("deleted_at", null)
        .range(args.offset || 0, (args.offset || 0) + (args.limit || 50) - 1);

      if (!memberships) return [];

      return memberships
        .map((m) => m.organizations)
        .filter((org) => org !== null);
    },
  },
};
