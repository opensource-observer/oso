import { createAdminClient } from "@/lib/supabase/admin";
import type { GraphQLResolverModule } from "@/app/api/v1/osograph/utils/types";
import {
  requireAuthentication,
  requireOrgMembership,
  getOrganization,
  getOrganizationByName,
  type GraphQLContext,
} from "@/app/api/v1/osograph/utils/auth";

export const organizationResolvers: GraphQLResolverModule<GraphQLContext> = {
  Query: {
    osoApp_organization: async (
      _: unknown,
      { orgName }: { orgName: string },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const org = await getOrganizationByName(orgName);
      await requireOrgMembership(authenticatedUser.userId, org.id);
      return org;
    },
  },

  Organization: {
    __resolveReference: async (reference: { id: string }) => {
      return getOrganization(reference.id);
    },

    orgName: (parent: { org_name: string }) => parent.org_name,
    createdAt: (parent: { created_at: string }) => parent.created_at,

    members: async (
      parent: { id: string },
      _args: unknown,
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      await requireOrgMembership(authenticatedUser.userId, parent.id);

      const supabase = createAdminClient();
      const { data: members } = await supabase
        .from("users_by_organization")
        .select("*")
        .eq("org_id", parent.id)
        .is("deleted_at", null);

      return members || [];
    },

    invitations: async (
      parent: { id: string },
      args: { status?: string },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      await requireOrgMembership(authenticatedUser.userId, parent.id);

      const supabase = createAdminClient();
      let query = supabase
        .from("invitations")
        .select("*")
        .eq("org_id", parent.id);

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
        query = query.is("deleted_at", null);
      }

      const { data: invitations } = await query;
      return invitations || [];
    },
  },
};
