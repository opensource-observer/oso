import { createAdminClient } from "@/lib/supabase/admin";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import {
  requireAuthentication,
  requireOrgMembership,
  getUserProfile,
  getOrganization,
  getOrganizationByName,
} from "@/app/api/v1/osograph/utils/auth";
import {
  OrganizationErrors,
  UserErrors,
  ServerErrors,
  createError,
  ErrorCode,
} from "@/app/api/v1/osograph/utils/errors";
import { getPaginationRange } from "@/app/api/v1/osograph/utils/resolvers";

export const organizationResolvers = {
  Query: {
    organizations: async (
      _: unknown,
      args: {
        limit?: number;
        offset?: number;
        where?: unknown;
        order_by?: unknown;
      },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const supabase = createAdminClient();

      const [start, end] = getPaginationRange(args);
      const { data: memberships } = await supabase
        .from("users_by_organization")
        .select("org_id, organizations(*)")
        .eq("user_id", authenticatedUser.userId)
        .is("deleted_at", null)
        .range(start, end);

      if (!memberships) return [];

      return memberships
        .map((m) => m.organizations)
        .filter((org) => org !== null);
    },

    organization: async (
      _: unknown,
      args: { id?: string; name?: string },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);

      if (!args.id && !args.name) {
        return null;
      }

      try {
        const org = args.id
          ? await getOrganization(args.id)
          : await getOrganizationByName(args.name!);

        await requireOrgMembership(authenticatedUser.userId, org.id);
        return org;
      } catch {
        return null;
      }
    },
  },

  Mutation: {
    addUserByEmail: async (
      _: unknown,
      args: { input: { orgId: string; email: string; role: string } },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const { input } = args;

      const supabase = createAdminClient();
      const org = await getOrganization(input.orgId);

      await requireOrgMembership(authenticatedUser.userId, org.id);

      const normalizedEmail = input.email.toLowerCase().trim();

      const { data: userProfile } = await supabase
        .from("user_profiles")
        .select("id")
        .ilike("email", normalizedEmail)
        .single();

      if (!userProfile) {
        throw UserErrors.notFound();
      }

      const { data: existingMember } = await supabase
        .from("users_by_organization")
        .select("id")
        .eq("user_id", userProfile.id)
        .eq("org_id", org.id)
        .is("deleted_at", null)
        .single();

      if (existingMember) {
        throw createError(
          ErrorCode.CONFLICT,
          "User is already a member of this organization",
        );
      }

      const { data: member, error } = await supabase
        .from("users_by_organization")
        .insert({
          org_id: org.id,
          user_id: userProfile.id,
          user_role: input.role.toLowerCase(),
        })
        .select()
        .single();

      if (error) {
        throw ServerErrors.database(
          `Failed to add user to organization: ${error.message}`,
        );
      }

      return {
        member,
        message: "User added to organization successfully",
        success: true,
      };
    },

    removeMember: async (
      _: unknown,
      args: { input: { orgId: string; userId: string } },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const { input } = args;

      if (input.userId === authenticatedUser.userId) {
        throw OrganizationErrors.cannotRemoveSelf();
      }

      const supabase = createAdminClient();
      const org = await getOrganization(input.orgId);
      await requireOrgMembership(authenticatedUser.userId, org.id);

      const { error } = await supabase
        .from("users_by_organization")
        .update({ deleted_at: new Date().toISOString() })
        .eq("user_id", input.userId)
        .eq("org_id", org.id)
        .is("deleted_at", null);

      if (error) {
        throw ServerErrors.database(
          `Failed to remove member from organization: ${error.message}`,
        );
      }

      return {
        message: "Member removed successfully",
        success: true,
      };
    },

    updateMemberRole: async (
      _: unknown,
      args: { input: { orgId: string; userId: string; role: string } },
      context: GraphQLContext,
    ) => {
      requireAuthentication(context.user);
      const { input } = args;

      const supabase = createAdminClient();
      const org = await getOrganization(input.orgId);

      const { data: member, error } = await supabase
        .from("users_by_organization")
        .update({ user_role: input.role.toLowerCase() })
        .eq("user_id", input.userId)
        .eq("org_id", org.id)
        .is("deleted_at", null)
        .select()
        .single();

      if (error) {
        throw ServerErrors.database(
          `Failed to update member role: ${error.message}`,
        );
      }

      return {
        member,
        message: "Member role updated successfully",
        success: true,
      };
    },
  },

  Organization: {
    name: (parent: { org_name: string }) => parent.org_name,
    displayName: (parent: { display_name: string | null }) =>
      parent.display_name,
    createdAt: (parent: { created_at: string }) => parent.created_at,
    updatedAt: (parent: { updated_at: string }) => parent.updated_at,

    members: async (
      parent: { id: string },
      args: { limit?: number; offset?: number },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      await requireOrgMembership(authenticatedUser.userId, parent.id);

      const supabase = createAdminClient();
      const [start, end] = getPaginationRange(args);
      const { data: members } = await supabase
        .from("users_by_organization")
        .select("*")
        .eq("org_id", parent.id)
        .is("deleted_at", null)
        .range(start, end);

      return members || [];
    },

    notebooks: async (
      parent: { id: string },
      args: {
        limit?: number;
        offset?: number;
        where?: unknown;
        order_by?: unknown;
      },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      await requireOrgMembership(authenticatedUser.userId, parent.id);

      const supabase = createAdminClient();
      const [start, end] = getPaginationRange(args);
      const { data: notebooks } = await supabase
        .from("notebooks")
        .select("*")
        .eq("org_id", parent.id)
        .is("deleted_at", null)
        .range(start, end);

      return notebooks || [];
    },

    datasets: async (
      parent: { id: string },
      args: {
        limit?: number;
        offset?: number;
        where?: unknown;
        order_by?: unknown;
      },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      await requireOrgMembership(authenticatedUser.userId, parent.id);

      const supabase = createAdminClient();
      const [start, end] = getPaginationRange(args);
      const { data: datasets } = await supabase
        .from("datasets")
        .select("*")
        .eq("org_id", parent.id)
        .is("deleted_at", null)
        .range(start, end);

      return datasets || [];
    },
  },

  OrganizationMember: {
    userId: (parent: { user_id: string }) => parent.user_id,
    orgId: (parent: { org_id: string }) => parent.org_id,
    userRole: (parent: { user_role: string }) => parent.user_role.toUpperCase(),
    createdAt: (parent: { created_at: string }) => parent.created_at,

    user: async (parent: { user_id: string }) => {
      return getUserProfile(parent.user_id);
    },
  },
};
