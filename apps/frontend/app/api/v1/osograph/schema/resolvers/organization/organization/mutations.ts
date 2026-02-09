import { getOrgScopedClient } from "@/app/api/v1/osograph/utils/access-control";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import {
  validateInput,
  AddUserByEmailSchema,
  RemoveMemberSchema,
  UpdateMemberRoleSchema,
} from "@/app/api/v1/osograph/utils/validation";
import {
  UserErrors,
  OrganizationErrors,
  ServerErrors,
} from "@/app/api/v1/osograph/utils/errors";
import { createError, ErrorCode } from "@/app/api/v1/osograph/utils/errors";
import {
  MutationAddUserByEmailArgs,
  MutationRemoveMemberArgs,
  MutationUpdateMemberRoleArgs,
} from "@/lib/graphql/generated/graphql";

export const organizationMemberMutations: GraphQLResolverModule<GraphQLContext>["Mutation"] =
  {
    addUserByEmail: async (
      _: unknown,
      args: MutationAddUserByEmailArgs,
      context: GraphQLContext,
    ) => {
      const input = validateInput(AddUserByEmailSchema, args.input);

      const { client } = await getOrgScopedClient(context, input.orgId);

      const normalizedEmail = input.email.toLowerCase().trim();

      const { data: userProfile } = await client
        .from("user_profiles")
        .select("id")
        .ilike("email", normalizedEmail)
        .single();

      if (!userProfile) {
        throw UserErrors.notFound();
      }

      const { data: existingMember } = await client
        .from("users_by_organization")
        .select("id")
        .eq("user_id", userProfile.id)
        .eq("org_id", input.orgId)
        .is("deleted_at", null)
        .single();

      if (existingMember) {
        throw createError(
          ErrorCode.CONFLICT,
          "User is already a member of this organization",
        );
      }

      const { data: member, error } = await client
        .from("users_by_organization")
        .insert({
          org_id: input.orgId,
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
      args: MutationRemoveMemberArgs,
      context: GraphQLContext,
    ) => {
      const input = validateInput(RemoveMemberSchema, args.input);

      const { client, userId: authenticatedUserId } = await getOrgScopedClient(
        context,
        input.orgId,
      );

      if (input.userId === authenticatedUserId) {
        throw OrganizationErrors.cannotRemoveSelf();
      }

      const { error } = await client
        .from("users_by_organization")
        .update({ deleted_at: new Date().toISOString() })
        .eq("user_id", input.userId)
        .eq("org_id", input.orgId)
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
      args: MutationUpdateMemberRoleArgs,
      context: GraphQLContext,
    ) => {
      const input = validateInput(UpdateMemberRoleSchema, args.input);

      const { client } = await getOrgScopedClient(context, input.orgId);

      const { data: member, error } = await client
        .from("users_by_organization")
        .update({ user_role: input.role.toLowerCase() })
        .eq("user_id", input.userId)
        .eq("org_id", input.orgId)
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
  };
