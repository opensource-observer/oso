import { v4 as uuid4 } from "uuid";
import { createAdminClient } from "@/lib/supabase/admin";
import { sendInvitationEmail } from "@/lib/services/email";
import { logger } from "@/lib/logger";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import {
  getOrganization,
  getUserProfile,
  requireAuthentication,
  requireOrgMembership,
} from "@/app/api/v1/osograph/utils/auth";
import {
  InvitationErrors,
  ServerErrors,
} from "@/app/api/v1/osograph/utils/errors";
import {
  requireOrganizationAccess,
  checkMembershipExists,
  preparePaginationRange,
  buildConnectionOrEmpty,
} from "@/app/api/v1/osograph/utils/resolver-helpers";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import {
  validateInput,
  CreateInvitationSchema,
  AcceptInvitationSchema,
  RevokeInvitationSchema,
  InvitationWhereSchema,
} from "@/app/api/v1/osograph/utils/validation";
import type {
  ConnectionArgs,
  FilterableConnectionArgs,
} from "@/app/api/v1/osograph/utils/pagination";
import {
  buildQuery,
  mergePredicates,
  type QueryPredicate,
} from "@/app/api/v1/osograph/utils/query-builder";
import { emptyConnection } from "@/app/api/v1/osograph/utils/connection";
import { queryWithPagination } from "@/app/api/v1/osograph/utils/query-helpers";

export async function getInvitationsConnection(
  orgIds: string | string[],
  args: ConnectionArgs,
  additionalPredicate?: Partial<QueryPredicate<"invitations">>,
) {
  const supabase = createAdminClient();
  const orgIdArray = Array.isArray(orgIds) ? orgIds : [orgIds];

  if (orgIdArray.length === 0) {
    return emptyConnection();
  }

  const [start, end] = preparePaginationRange(args);

  const basePredicate: Partial<QueryPredicate<"invitations">> = {
    in: [{ key: "org_id", value: orgIdArray }],
  };

  const predicate = additionalPredicate
    ? mergePredicates(basePredicate, additionalPredicate)
    : basePredicate;

  const {
    data: invitations,
    count,
    error,
  } = await buildQuery(supabase, "invitations", predicate, (query) =>
    query.range(start, end),
  );

  if (error) {
    throw ServerErrors.database(
      `Failed to fetch invitations: ${error.message}`,
    );
  }

  return buildConnectionOrEmpty(invitations, args, count);
}

export const invitationResolvers: GraphQLResolverModule<GraphQLContext> = {
  Query: {
    invitations: async (
      _: unknown,
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      return queryWithPagination(args, context, {
        tableName: "invitations",
        whereSchema: InvitationWhereSchema,
        requireAuth: true,
        filterByUserOrgs: true,
        buildBasePredicate: ({ userOrgIds }) => ({
          in: [{ key: "org_id", value: userOrgIds }],
        }),
      });
    },
  },

  Mutation: {
    createInvitation: async (
      _: unknown,
      args: { input: { orgId: string; email: string; role: string } },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const input = validateInput(CreateInvitationSchema, args.input);

      const supabase = createAdminClient();
      const org = await requireOrganizationAccess(
        authenticatedUser.userId,
        input.orgId,
      );
      const userProfile = await getUserProfile(authenticatedUser.userId);

      const normalizedEmail = input.email.toLowerCase().trim();

      if (authenticatedUser.email?.toLowerCase() === normalizedEmail) {
        throw InvitationErrors.cannotInviteSelf();
      }

      const { data: existingUser } = await supabase
        .from("user_profiles")
        .select("id")
        .ilike("email", normalizedEmail)
        .single();

      if (existingUser) {
        const membershipExists = await checkMembershipExists(
          existingUser.id,
          org.id,
        );

        if (membershipExists) {
          throw InvitationErrors.alreadyExists();
        }
      }

      const { data: existingInvitation } = await supabase
        .from("invitations")
        .select("id, expires_at")
        .eq("org_id", org.id)
        .ilike("email", normalizedEmail)
        .is("accepted_at", null)
        .is("deleted_at", null)
        .gt("expires_at", new Date().toISOString())
        .single();

      if (existingInvitation) {
        throw InvitationErrors.alreadyExists();
      }

      const invitationId = uuid4();

      const { data: invitation, error } = await supabase
        .from("invitations")
        .insert({
          id: invitationId,
          email: normalizedEmail,
          org_id: org.id,
          org_name: org.org_name,
          invited_by: userProfile.id,
        })
        .select()
        .single();

      if (error) {
        logger.error("Database error:", error);
        throw ServerErrors.database(
          `Failed to create invitation: ${error.message}`,
        );
      }

      try {
        await sendInvitationEmail({
          to: normalizedEmail,
          orgName: org.org_name,
          inviteToken: invitationId,
          inviterName: userProfile.full_name || userProfile.email || "Someone",
        });
      } catch (emailError) {
        logger.error("Failed to send invitation email:", emailError);
        throw ServerErrors.externalService(
          `Failed to send invitation email: ${
            emailError instanceof Error ? emailError.message : "Unknown error"
          }`,
        );
      }

      return {
        invitation,
        message: `Invitation sent to ${normalizedEmail}`,
        success: true,
      };
    },

    acceptInvitation: async (
      _: unknown,
      args: { input: { invitationId: string } },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const input = validateInput(AcceptInvitationSchema, args.input);

      const supabase = createAdminClient();

      const { data: invitation, error: invError } = await supabase
        .from("invitations")
        .select("*")
        .eq("id", input.invitationId)
        .single();

      if (invError || !invitation) {
        throw InvitationErrors.notFound();
      }

      if (invitation.accepted_at) {
        throw InvitationErrors.alreadyAccepted();
      }

      if (invitation.deleted_at) {
        throw InvitationErrors.revoked();
      }

      if (new Date(invitation.expires_at) < new Date()) {
        throw InvitationErrors.expired();
      }

      const userEmail = authenticatedUser.email?.toLowerCase();
      if (userEmail !== invitation.email.toLowerCase()) {
        throw InvitationErrors.wrongRecipient();
      }

      const { data: existingMembership } = await supabase
        .from("users_by_organization")
        .select("*")
        .eq("user_id", authenticatedUser.userId)
        .eq("org_id", invitation.org_id)
        .is("deleted_at", null)
        .single();

      if (existingMembership) {
        throw InvitationErrors.alreadyAccepted();
      }

      const { error: acceptError } = await supabase
        .from("invitations")
        .update({
          accepted_at: new Date().toISOString(),
          accepted_by: authenticatedUser.userId,
        })
        .eq("id", input.invitationId);

      if (acceptError) {
        throw ServerErrors.database(
          `Failed to accept invitation: ${acceptError.message}`,
        );
      }

      const { data: member, error: memberError } = await supabase
        .from("users_by_organization")
        .insert({
          user_id: authenticatedUser.userId,
          org_id: invitation.org_id,
          user_role: "admin",
        })
        .select()
        .single();

      if (memberError) {
        logger.error("Failed to create membership:", memberError);
        throw ServerErrors.database(
          `Failed to create membership: ${memberError.message}`,
        );
      }

      return {
        member,
        message: "Invitation accepted successfully",
        success: true,
      };
    },

    revokeInvitation: async (
      _: unknown,
      args: { input: { invitationId: string } },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const input = validateInput(RevokeInvitationSchema, args.input);

      const supabase = createAdminClient();

      const { data: invitation, error: invError } = await supabase
        .from("invitations")
        .select("*")
        .eq("id", input.invitationId)
        .single();

      if (invError || !invitation) {
        throw InvitationErrors.notFound();
      }

      await requireOrgMembership(authenticatedUser.userId, invitation.org_id);

      const { error } = await supabase
        .from("invitations")
        .update({ deleted_at: new Date().toISOString() })
        .eq("id", input.invitationId);

      if (error) {
        throw ServerErrors.database(
          `Failed to revoke invitation: ${error.message}`,
        );
      }

      return {
        message: "Invitation revoked successfully",
        success: true,
      };
    },
  },

  Invitation: {
    orgId: (parent: { org_id: string }) => parent.org_id,

    status: (parent: {
      accepted_at: string | null;
      deleted_at: string | null;
      expires_at: string;
    }) => {
      if (parent.deleted_at) return "REVOKED";
      if (parent.accepted_at) return "ACCEPTED";
      if (new Date(parent.expires_at) < new Date()) return "EXPIRED";
      return "PENDING";
    },

    createdAt: (parent: { created_at: string }) => parent.created_at,
    expiresAt: (parent: { expires_at: string }) => parent.expires_at,
    acceptedAt: (parent: { accepted_at: string | null }) => parent.accepted_at,
    deletedAt: (parent: { deleted_at: string | null }) => parent.deleted_at,

    organization: async (parent: { org_id: string }) => {
      return getOrganization(parent.org_id);
    },

    invitedBy: async (parent: { invited_by: string }) => {
      return getUserProfile(parent.invited_by);
    },

    acceptedBy: async (parent: { accepted_by: string | null }) => {
      if (!parent.accepted_by) return null;
      return getUserProfile(parent.accepted_by);
    },

    userRole: (parent: { user_role: string | undefined }) =>
      parent.user_role?.toUpperCase() || "admin".toUpperCase(),
  },
};
