import { createAdminClient } from "@/lib/supabase/admin";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import {
  buildConnection,
  emptyConnection,
} from "@/app/api/v1/osograph/utils/connection";
import type { ConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import {
  getFetchLimit,
  getSupabaseRange,
} from "@/app/api/v1/osograph/utils/pagination";

export const userResolvers = {
  User: {
    fullName: (parent: { full_name: string | null }) => parent.full_name,
    avatarUrl: (parent: { avatar_url: string | null }) => parent.avatar_url,

    organizations: async (
      parent: { id: string },
      args: ConnectionArgs & {
        where?: unknown;
        order_by?: unknown;
      },
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
  },
};
