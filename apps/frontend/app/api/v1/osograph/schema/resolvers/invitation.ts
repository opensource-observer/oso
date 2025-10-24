import { v4 as uuid4 } from "uuid";
import { createAdminClient } from "@/lib/supabase/admin";
import { sendInvitationEmail } from "@/lib/services/email";
import { logger } from "@/lib/logger";
import type { GraphQLResolverMap } from "@apollo/subgraph/dist/schema-helper/resolverMap";
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
  CreateInvitationSchema,
  AcceptInvitationSchema,
  RevokeInvitationSchema,
} from "@/app/api/v1/osograph/utils/validation";
import {
  InvitationErrors,
  UserErrors,
  ServerErrors,
} from "@/app/api/v1/osograph/utils/errors";

export const invitationResolvers: GraphQLResolverMap<GraphQLContext> = {
  Query: {
    osoApp_invitation: async (
      _: unknown,
      { id }: { id: string },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const supabase = createAdminClient();
      const { data: invitation, error } = await supabase
        .from("invitations")
        .select("*")
        .eq("id", id)
        .single();

      if (error || !invitation) {
        throw InvitationErrors.notFound();
      }

      const { data: membership } = await supabase
        .from("users_by_organization")
        .select("id")
        .eq("user_id", authenticatedUser.userId)
        .eq("org_id", invitation.org_id)
        .is("deleted_at", null)
        .single();

      const userEmail = authenticatedUser.email?.toLowerCase();
      const isInvitee = userEmail === invitation.email.toLowerCase();

      if (!membership && !isInvitee) {
        throw InvitationErrors.wrongRecipient();
      }

      return invitation;
    },

    osoApp_myInvitations: async (
      _: unknown,
      args: { status?: string },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const supabase = createAdminClient();
      const userEmail = authenticatedUser.email?.toLowerCase();

      if (!userEmail) {
        throw UserErrors.emailNotFound();
      }

      let query = supabase
        .from("invitations")
        .select("*")
        .ilike("email", userEmail);

      if (args.status) {
        switch (args.status) {
          case "PENDING":
            query = query
              .is("accepted_at", null)
              .is("deleted_at", null)
              .gt("expires_at", new Date().toISOString());
            break;
          case "ACCEPTED":
            query = query.not("accepted_at", "is", null);
            break;
          case "EXPIRED":
            query = query
              .is("accepted_at", null)
              .is("deleted_at", null)
              .lt("expires_at", new Date().toISOString());
            break;
          case "DELETED":
            query = query.not("deleted_at", "is", null);
            break;
        }
      } else {
        query = query
          .is("accepted_at", null)
          .is("deleted_at", null)
          .gt("expires_at", new Date().toISOString());
      }

      const { data: invitations } = await query;
      return invitations || [];
    },
  },

  Invitation: {
    __resolveReference: async (reference: { id: string }) => {
      const supabase = createAdminClient();
      const { data: invitation } = await supabase
        .from("invitations")
        .select("*")
        .eq("id", reference.id)
        .single();

      return invitation;
    },

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

    status: (parent: {
      accepted_at: string | null;
      deleted_at: string | null;
      expires_at: string;
    }) => {
      if (parent.deleted_at) return "DELETED";
      if (parent.accepted_at) return "ACCEPTED";
      if (new Date(parent.expires_at) < new Date()) return "EXPIRED";
      return "PENDING";
    },

    createdAt: (parent: { created_at: string }) => parent.created_at,
    expiresAt: (parent: { expires_at: string }) => parent.expires_at,
    acceptedAt: (parent: { accepted_at: string | null }) => parent.accepted_at,
  },

  Mutation: {
    osoApp_createInvitation: async (
      _: unknown,
      { input }: { input: { email: string; orgName: string } },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const validated = validateInput(CreateInvitationSchema, input);
      const normalizedEmail = validated.email.toLowerCase().trim();

      const supabase = createAdminClient();

      const userProfile = await getUserProfile(authenticatedUser.userId);

      const org = await getOrganizationByName(validated.orgName);

      await requireOrgMembership(authenticatedUser.userId, org.id);

      if (authenticatedUser.email?.toLowerCase() === normalizedEmail) {
        throw InvitationErrors.cannotInviteSelf();
      }

      const { data: existingUser } = await supabase
        .from("user_profiles")
        .select("id")
        .ilike("email", normalizedEmail)
        .single();

      if (existingUser) {
        const { data: existingMembership } = await supabase
          .from("users_by_organization")
          .select("*")
          .eq("user_id", existingUser.id)
          .eq("org_id", org.id)
          .is("deleted_at", null)
          .single();

        if (existingMembership) {
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
          org_name: org.org_name,
          org_id: org.id,
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
          `Failed to send invitation email: ${emailError instanceof Error ? emailError.message : "Unknown error"}`,
        );
      }

      return {
        invitation,
        message: `Invitation sent to ${normalizedEmail}`,
        success: true,
      };
    },

    osoApp_acceptInvitation: async (
      _: unknown,
      args: { invitationId: string },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const validated = validateInput(AcceptInvitationSchema, args);

      const supabase = createAdminClient();

      const { data: invitation, error: invError } = await supabase
        .from("invitations")
        .select("*")
        .eq("id", validated.invitationId)
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
        .eq("id", validated.invitationId);

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
          user_role: "member",
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

    osoApp_revokeInvitation: async (
      _: unknown,
      args: { invitationId: string },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const validated = validateInput(RevokeInvitationSchema, args);

      const supabase = createAdminClient();

      const { data: invitation, error: invError } = await supabase
        .from("invitations")
        .select("*")
        .eq("id", validated.invitationId)
        .single();

      if (invError || !invitation) {
        throw InvitationErrors.notFound();
      }

      await requireOrgMembership(authenticatedUser.userId, invitation.org_id);

      const { error } = await supabase
        .from("invitations")
        .update({ deleted_at: new Date().toISOString() })
        .eq("id", validated.invitationId);

      if (error) {
        throw ServerErrors.database(
          `Failed to revoke invitation: ${error.message}`,
        );
      }

      return {
        invitationId: validated.invitationId,
        message: "Invitation revoked successfully",
        success: true,
      };
    },
  },
};
