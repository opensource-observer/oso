import { createAdminClient } from "@/lib/supabase/admin";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { requireAuthentication } from "@/app/api/v1/osograph/utils/auth";
import { UserErrors } from "@/app/api/v1/osograph/utils/errors";
import type { FilterableConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import {
  getUserOrganizationsConnection,
  getUserInvitationsConnection,
  getUserOrganizationIds,
} from "@/app/api/v1/osograph/utils/resolver-helpers";
import {
  validateInput,
  OrganizationWhereSchema,
  NotebookWhereSchema,
  DatasetWhereSchema,
  InvitationWhereSchema,
} from "@/app/api/v1/osograph/utils/validation";
import { parseWhereClause } from "@/app/api/v1/osograph/utils/where-parser";
import { queryWithPagination } from "@/app/api/v1/osograph/utils/query-helpers";

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
      args: FilterableConnectionArgs,
      _context: GraphQLContext,
    ) => {
      const validatedWhere = args.where
        ? validateInput(OrganizationWhereSchema, args.where)
        : undefined;

      return getUserOrganizationsConnection(
        parent.id,
        args,
        validatedWhere ? parseWhereClause(validatedWhere) : undefined,
      );
    },

    notebooks: async (
      parent: { id: string },
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      const orgIds = await getUserOrganizationIds(parent.id);

      return queryWithPagination(args, context, {
        tableName: "notebooks",
        whereSchema: NotebookWhereSchema,
        requireAuth: false,
        filterByUserOrgs: false,
        parentOrgIds: orgIds,
        basePredicate: {
          is: [{ key: "deleted_at", value: null }],
        },
      });
    },

    datasets: async (
      parent: { id: string },
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      const orgIds = await getUserOrganizationIds(parent.id);

      return queryWithPagination(args, context, {
        tableName: "datasets",
        whereSchema: DatasetWhereSchema,
        requireAuth: false,
        filterByUserOrgs: false,
        parentOrgIds: orgIds,
        basePredicate: {
          is: [{ key: "deleted_at", value: null }],
        },
      });
    },

    invitations: async (
      parent: { id: string; email: string },
      args: FilterableConnectionArgs,
      _context: GraphQLContext,
    ) => {
      const validatedWhere = args.where
        ? validateInput(InvitationWhereSchema, args.where)
        : undefined;

      return getUserInvitationsConnection(
        parent.email,
        args,
        validatedWhere ? parseWhereClause(validatedWhere) : undefined,
      );
    },
  },
};
