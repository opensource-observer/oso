import { getAuthenticatedClient } from "@/app/api/v1/osograph/utils/access-control";
import { logger } from "@/lib/logger";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import {
  validateInput,
  AcceptInvitationSchema,
} from "@/app/api/v1/osograph/utils/validation";
import {
  InvitationErrors,
  ServerErrors,
} from "@/app/api/v1/osograph/utils/errors";
import { MutationAcceptInvitationArgs } from "@/lib/graphql/generated/graphql";

export const invitationMutations: GraphQLResolverModule<GraphQLContext>["Mutation"] =
  {
    acceptInvitation: async (
      _: unknown,
      args: MutationAcceptInvitationArgs,
      context: GraphQLContext,
    ) => {
      const input = validateInput(AcceptInvitationSchema, args.input);
      const { client, userId } = await getAuthenticatedClient(context);

      const { data: invitation, error: invError } = await client
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

      // Verify the authenticated user's email matches the invitation
      if (context.user.role !== "user" || !context.user.email) {
        throw InvitationErrors.wrongRecipient();
      }

      const userEmail = context.user.email.toLowerCase();
      if (userEmail !== invitation.email.toLowerCase()) {
        throw InvitationErrors.wrongRecipient();
      }

      const { data: existingMembership } = await client
        .from("users_by_organization")
        .select("*")
        .eq("user_id", userId)
        .eq("org_id", invitation.org_id)
        .is("deleted_at", null)
        .single();

      if (existingMembership) {
        throw InvitationErrors.alreadyAccepted();
      }

      const { error: acceptError } = await client
        .from("invitations")
        .update({
          accepted_at: new Date().toISOString(),
          accepted_by: userId,
        })
        .eq("id", input.invitationId);

      if (acceptError) {
        throw ServerErrors.database(
          `Failed to accept invitation: ${acceptError.message}`,
        );
      }

      const { data: member, error: memberError } = await client
        .from("users_by_organization")
        .insert({
          user_id: userId,
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
  };
