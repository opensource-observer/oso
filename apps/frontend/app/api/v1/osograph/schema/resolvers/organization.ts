import { createAdminClient } from "@/lib/supabase/admin";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import {
  getOrganization,
  getUserProfile,
  requireAuthentication,
  requireOrgMembership,
} from "@/app/api/v1/osograph/utils/auth";
import {
  createError,
  ErrorCode,
  OrganizationErrors,
  ServerErrors,
  UserErrors,
} from "@/app/api/v1/osograph/utils/errors";
import type { FilterableConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import {
  buildConnectionOrEmpty,
  getUserOrganizationsConnection,
  preparePaginationRange,
} from "@/app/api/v1/osograph/utils/resolver-helpers";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import {
  AddUserByEmailSchema,
  DatasetWhereSchema,
  NotebookWhereSchema,
  OrganizationWhereSchema,
  RemoveMemberSchema,
  UpdateMemberRoleSchema,
  validateInput,
} from "@/app/api/v1/osograph/utils/validation";
import { parseWhereClause } from "@/app/api/v1/osograph/utils/where-parser";
import { queryWithPagination } from "@/app/api/v1/osograph/utils/query-helpers";

export const organizationResolvers: GraphQLResolverModule<GraphQLContext> = {
  Query: {
    organizations: async (
      _: unknown,
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);

      const validatedWhere = args.where
        ? validateInput(OrganizationWhereSchema, args.where)
        : undefined;

      return getUserOrganizationsConnection(
        authenticatedUser.userId,
        args,
        validatedWhere ? parseWhereClause(validatedWhere) : undefined,
      );
    },
  },

  Mutation: {
    addUserByEmail: async (
      _: unknown,
      args: { input: { orgId: string; email: string; role: string } },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const input = validateInput(AddUserByEmailSchema, args.input);

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
      const input = validateInput(RemoveMemberSchema, args.input);

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
      const input = validateInput(UpdateMemberRoleSchema, args.input);

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
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      await requireOrgMembership(authenticatedUser.userId, parent.id);

      const supabase = createAdminClient();
      const [start, end] = preparePaginationRange(args);

      const { data: membersData, count } = await supabase
        .from("users_by_organization")
        .select("*, user_profiles(*)", { count: "exact" })
        .eq("org_id", parent.id)
        .is("deleted_at", null)
        .range(start, end);

      if (!membersData || membersData.length === 0) {
        return buildConnectionOrEmpty(null, args, count);
      }

      const users = membersData
        .map((m) => m.user_profiles)
        .filter((user) => user !== null);

      return buildConnectionOrEmpty(users, args, count);
    },

    notebooks: async (
      parent: { id: string },
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      await requireOrgMembership(authenticatedUser.userId, parent.id);

      return queryWithPagination(args, context, {
        tableName: "notebooks",
        whereSchema: NotebookWhereSchema,
        requireAuth: false,
        filterByUserOrgs: false,
        parentOrgIds: parent.id,
        buildBasePredicate: ({ parentOrgIds }) => ({
          in: [{ key: "org_id", value: parentOrgIds }],
          is: [{ key: "deleted_at", value: null }],
        }),
      });
    },

    datasets: async (
      parent: { id: string },
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      await requireOrgMembership(authenticatedUser.userId, parent.id);

      return queryWithPagination(args, context, {
        tableName: "datasets",
        whereSchema: DatasetWhereSchema,
        requireAuth: false,
        filterByUserOrgs: false,
        parentOrgIds: parent.id,
        buildBasePredicate: ({ parentOrgIds }) => ({
          in: [{ key: "org_id", value: parentOrgIds }],
          is: [{ key: "deleted_at", value: null }],
        }),
      });
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
