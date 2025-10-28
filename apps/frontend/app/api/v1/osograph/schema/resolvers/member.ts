import { createAdminClient } from "@/lib/supabase/admin";
import type { GraphQLResolverModule } from "@/app/api/v1/osograph/utils/types";
import {
  requireAuthentication,
  requireOrgMembership,
  getUserProfile,
  getOrganization,
  getOrganizationByName,
  type GraphQLContext,
} from "@/app/api/v1/osograph/utils/auth";
import {
  validateInput,
  RemoveMemberSchema,
  UpdateMemberRoleSchema,
  AddUserByEmailSchema,
} from "@/app/api/v1/osograph/utils/validation";
import {
  OrganizationErrors,
  UserErrors,
  ServerErrors,
  createError,
  ErrorCode,
} from "@/app/api/v1/osograph/utils/errors";

export const memberResolvers: GraphQLResolverModule<GraphQLContext> = {
  OrganizationMember: {
    __resolveReference: async (reference: { id: string }) => {
      const supabase = createAdminClient();
      const { data: member } = await supabase
        .from("users_by_organization")
        .select("*")
        .eq("id", reference.id)
        .single();

      return member;
    },

    user: async (parent: { user_id: string }) => {
      return getUserProfile(parent.user_id);
    },

    organization: async (parent: { org_id: string }) => {
      return getOrganization(parent.org_id);
    },

    userId: (parent: { user_id: string }) => parent.user_id,
    role: (parent: { user_role: string }) => parent.user_role.toUpperCase(),
    joinedAt: (parent: { created_at: string }) => parent.created_at,
  },

  Mutation: {
    osoApp_removeMember: async (
      _: unknown,
      args: { orgName: string; userId: string },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const validated = validateInput(RemoveMemberSchema, args);
      const org = await getOrganizationByName(validated.orgName);

      if (validated.userId === authenticatedUser.userId) {
        throw OrganizationErrors.cannotRemoveSelf();
      }

      const supabase = createAdminClient();

      const { error } = await supabase
        .from("users_by_organization")
        .update({ deleted_at: new Date().toISOString() })
        .eq("user_id", validated.userId)
        .eq("org_id", org.id)
        .is("deleted_at", null);

      if (error) {
        throw ServerErrors.database(
          `Failed to remove member from organization: ${error.message}`,
        );
      }

      return {
        userId: validated.userId,
        orgName: validated.orgName,
        message: "Member removed successfully",
        success: true,
      };
    },

    osoApp_updateMemberRole: async (
      _: unknown,
      args: { orgName: string; userId: string; role: string },
      context: GraphQLContext,
    ) => {
      requireAuthentication(context.user);
      const validated = validateInput(UpdateMemberRoleSchema, args);
      const org = await getOrganizationByName(validated.orgName);

      const supabase = createAdminClient();

      const { data: member, error } = await supabase
        .from("users_by_organization")
        .update({ user_role: validated.role.toLowerCase() })
        .eq("user_id", validated.userId)
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

    osoApp_addUserByEmail: async (
      _: unknown,
      args: { orgName: string; email: string; role: string },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const validated = validateInput(AddUserByEmailSchema, args);
      const org = await getOrganizationByName(validated.orgName);

      await requireOrgMembership(authenticatedUser.userId, org.id);

      const supabase = createAdminClient();

      const normalizedEmail = validated.email.toLowerCase().trim();

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
          "Cannot add user to organization",
        );
      }

      const { data: member, error } = await supabase
        .from("users_by_organization")
        .insert({
          org_id: org.id,
          user_id: userProfile.id,
          user_role: validated.role.toLowerCase(),
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
  },
};
