import { createAdminClient } from "@/lib/supabase/admin";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { requireAuthentication } from "@/app/api/v1/osograph/utils/auth";
import { UserErrors } from "@/app/api/v1/osograph/utils/errors";
import { getPaginationRange } from "@/app/api/v1/osograph/utils/resolvers";

export const viewerResolvers = {
  Query: {
    viewer: async (_: unknown, _args: unknown, context: GraphQLContext) => {
      const authenticatedUser = requireAuthentication(context.user);
      const supabase = createAdminClient();

      const { data: profile, error } = await supabase
        .from("user_profiles")
        .select("*")
        .eq("id", authenticatedUser.userId)
        .single();

      if (error || !profile) {
        throw UserErrors.profileNotFound();
      }

      return profile;
    },
  },

  Viewer: {
    fullName: (parent: { full_name: string | null }) => parent.full_name,
    avatarUrl: (parent: { avatar_url: string | null }) => parent.avatar_url,

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
      const [start, end] = getPaginationRange(args);
      const { data: memberships } = await supabase
        .from("users_by_organization")
        .select("org_id, organizations(*)")
        .eq("user_id", parent.id)
        .is("deleted_at", null)
        .range(start, end);

      if (!memberships) return [];

      return memberships
        .map((m) => m.organizations)
        .filter((org) => org !== null);
    },

    notebooks: async (
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
        .select("org_id")
        .eq("user_id", parent.id)
        .is("deleted_at", null);

      const orgIds = memberships?.map((m) => m.org_id) || [];
      if (orgIds.length === 0) {
        return [];
      }

      const [start, end] = getPaginationRange(args);
      const { data: notebooks } = await supabase
        .from("notebooks")
        .select("*")
        .in("org_id", orgIds)
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
      _context: GraphQLContext,
    ) => {
      const supabase = createAdminClient();

      const { data: memberships } = await supabase
        .from("users_by_organization")
        .select("org_id")
        .eq("user_id", parent.id)
        .is("deleted_at", null);

      const orgIds = memberships?.map((m) => m.org_id) || [];
      if (orgIds.length === 0) {
        return [];
      }

      const [start, end] = getPaginationRange(args);
      const { data: datasets } = await supabase
        .from("datasets")
        .select("*")
        .in("org_id", orgIds)
        .is("deleted_at", null)
        .range(start, end);

      return datasets || [];
    },

    invitations: async (
      parent: { id: string; email: string },
      args: {
        limit?: number;
        offset?: number;
        where?: unknown;
        order_by?: unknown;
      },
      _context: GraphQLContext,
    ) => {
      const supabase = createAdminClient();
      const userEmail = parent.email?.toLowerCase();

      if (!userEmail) {
        return [];
      }

      const [start, end] = getPaginationRange(args);
      const { data: invitations } = await supabase
        .from("invitations")
        .select("*")
        .ilike("email", userEmail)
        .is("accepted_at", null)
        .is("deleted_at", null)
        .gt("expires_at", new Date().toISOString())
        .range(start, end);

      return invitations || [];
    },
  },
};
