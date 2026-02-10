import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import {
  getUserOrganizationIds,
  getUserOrganizationsConnection,
  getUserInvitationsConnection,
} from "@/app/api/v1/osograph/utils/resolver-helpers";
import {
  ExplicitClientQueryOptions,
  queryWithPagination,
} from "@/app/api/v1/osograph/utils/query-helpers";
import { FilterableConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import {
  OrganizationWhereSchema,
  NotebookWhereSchema,
  DatasetWhereSchema,
  InvitationWhereSchema,
  validateInput,
} from "@/app/api/v1/osograph/utils/validation";
import { parseWhereClause } from "@/app/api/v1/osograph/utils/where-parser";
import { UserProfilesRow } from "@/lib/types/schema-types";
import { getAuthenticatedClient } from "@/app/api/v1/osograph/utils/access-control";

/**
 * Type resolvers for Viewer.
 * These field resolvers don't require auth checks as they operate on
 * already-fetched viewer data.
 */
export const viewerTypeResolvers: GraphQLResolverModule<GraphQLContext> = {
  Viewer: {
    fullName: (parent: UserProfilesRow) => parent.full_name,
    avatarUrl: (parent: UserProfilesRow) => parent.avatar_url,

    organizations: async (
      parent: UserProfilesRow,
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      const { client } = getAuthenticatedClient(context);

      const validatedWhere = args.where
        ? validateInput(OrganizationWhereSchema, args.where)
        : undefined;

      return getUserOrganizationsConnection(
        parent.id,
        args,
        validatedWhere ? parseWhereClause(validatedWhere) : {},
        client,
      );
    },

    notebooks: async (
      parent: UserProfilesRow,
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      const { client } = getAuthenticatedClient(context);
      const orgIds = await getUserOrganizationIds(parent.id, client);

      const options: ExplicitClientQueryOptions<"notebooks"> = {
        client,
        orgIds,
        tableName: "notebooks",
        whereSchema: NotebookWhereSchema,
        basePredicate: {
          is: [{ key: "deleted_at", value: null }],
        },
      };

      return queryWithPagination(args, context, options);
    },

    datasets: async (
      parent: UserProfilesRow,
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      const { client } = getAuthenticatedClient(context);
      const orgIds = await getUserOrganizationIds(parent.id, client);

      const options: ExplicitClientQueryOptions<"datasets"> = {
        client,
        orgIds,
        tableName: "datasets",
        whereSchema: DatasetWhereSchema,
        basePredicate: {
          is: [{ key: "deleted_at", value: null }],
        },
      };

      return queryWithPagination(args, context, options);
    },

    invitations: async (
      parent: UserProfilesRow,
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      const { client } = getAuthenticatedClient(context);

      const validatedWhere = args.where
        ? validateInput(InvitationWhereSchema, args.where)
        : undefined;

      return getUserInvitationsConnection(
        parent.email,
        args,
        validatedWhere ? parseWhereClause(validatedWhere) : {},
        client,
      );
    },
  },
};
