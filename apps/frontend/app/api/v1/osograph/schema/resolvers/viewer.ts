import { createAdminClient } from "@/lib/supabase/admin";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { requireAuthentication } from "@/app/api/v1/osograph/utils/auth";
import { UserErrors } from "@/app/api/v1/osograph/utils/errors";
import {
  buildConnection,
  emptyConnection,
} from "@/app/api/v1/osograph/utils/connection";
import type { ConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import {
  getFetchLimit,
  getSupabaseRange,
} from "@/app/api/v1/osograph/utils/pagination";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";

export const viewerResolvers: GraphQLResolverModule<GraphQLContext> = {
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
      args: ConnectionArgs,
      _context: GraphQLContext,
    ) => {
      const supabase = createAdminClient();
      const limit = getFetchLimit(args);
      const [start, end] = getSupabaseRange({
        ...args,
        first: limit,
      });

      const { data: memberships } = await supabase
        .from("users_by_organization")
        .select("org_id, organizations(*)")
        .eq("user_id", parent.id)
        .is("deleted_at", null)
        .range(start, end);

      if (!memberships || memberships.length === 0) {
        return emptyConnection();
      }

      const organizations = memberships
        .map((m) => m.organizations)
        .filter((org) => org !== null);

      return buildConnection(organizations, args);
    },

    notebooks: async (
      parent: { id: string },
      args: ConnectionArgs,
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
        return emptyConnection();
      }

      const limit = getFetchLimit(args);
      const [start, end] = getSupabaseRange({
        ...args,
        first: limit,
      });

      const { data: notebooks } = await supabase
        .from("notebooks")
        .select("*")
        .in("org_id", orgIds)
        .is("deleted_at", null)
        .range(start, end);

      if (!notebooks || notebooks.length === 0) {
        return emptyConnection();
      }

      return buildConnection(notebooks, args);
    },

    datasets: async (
      parent: { id: string },
      args: ConnectionArgs,
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
        return emptyConnection();
      }

      const limit = getFetchLimit(args);
      const [start, end] = getSupabaseRange({
        ...args,
        first: limit,
      });

      const { data: datasets } = await supabase
        .from("datasets")
        .select("*")
        .in("org_id", orgIds)
        .is("deleted_at", null)
        .range(start, end);

      if (!datasets || datasets.length === 0) {
        return emptyConnection();
      }

      return buildConnection(datasets, args);
    },

    invitations: async (
      parent: { id: string; email: string },
      args: ConnectionArgs,
      _context: GraphQLContext,
    ) => {
      const supabase = createAdminClient();
      const userEmail = parent.email?.toLowerCase();

      if (!userEmail) {
        return emptyConnection();
      }

      const limit = getFetchLimit(args);
      const [start, end] = getSupabaseRange({
        ...args,
        first: limit,
      });

      const { data: invitations } = await supabase
        .from("invitations")
        .select("*")
        .ilike("email", userEmail)
        .is("accepted_at", null)
        .is("deleted_at", null)
        .gt("expires_at", new Date().toISOString())
        .range(start, end);

      if (!invitations || invitations.length === 0) {
        return emptyConnection();
      }

      return buildConnection(invitations, args);
    },
  },
};
