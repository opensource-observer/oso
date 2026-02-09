import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import {
  getOrganization,
  getUserProfile,
} from "@/app/api/v1/osograph/utils/auth";
import { getAuthenticatedClient } from "@/app/api/v1/osograph/utils/access-control";
import { InvitationsRow } from "@/lib/types/schema-types";

/**
 * Type resolvers for Invitation in user context.
 * These field resolvers don't require auth checks as they operate on
 * already-fetched invitation data. Uses getAuthenticatedClient since
 * these are accessed from user-level queries.
 */
export const invitationTypeResolvers: GraphQLResolverModule<GraphQLContext> = {
  Invitation: {
    orgId: (parent: InvitationsRow) => parent.org_id,

    status: (parent: InvitationsRow) => {
      if (parent.deleted_at) return "REVOKED";
      if (parent.accepted_at) return "ACCEPTED";
      if (new Date(parent.expires_at) < new Date()) return "EXPIRED";
      return "PENDING";
    },

    createdAt: (parent: InvitationsRow) => parent.created_at,
    expiresAt: (parent: InvitationsRow) => parent.expires_at,
    acceptedAt: (parent: InvitationsRow) => parent.accepted_at,
    deletedAt: (parent: InvitationsRow) => parent.deleted_at,

    organization: async (
      parent: InvitationsRow,
      _args: unknown,
      context: GraphQLContext,
    ) => {
      const { client } = getAuthenticatedClient(context);
      return getOrganization(parent.org_id, client);
    },

    invitedBy: async (
      parent: InvitationsRow,
      _args: unknown,
      context: GraphQLContext,
    ) => {
      const { client } = getAuthenticatedClient(context);
      return getUserProfile(parent.invited_by, client);
    },

    acceptedBy: async (
      parent: InvitationsRow,
      _args: unknown,
      context: GraphQLContext,
    ) => {
      const { client } = getAuthenticatedClient(context);
      if (!parent.accepted_by) return null;
      return getUserProfile(parent.accepted_by, client);
    },

    // TODO(jabolo): Add user_role column to invitations table and return actual role in invitation. (#6567)
    userRole: () => "admin",
  },
};
