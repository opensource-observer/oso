import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import { getUserProfile } from "@/app/api/v1/osograph/utils/auth";
import {
  ExplicitClientQueryOptions,
  queryWithPagination,
} from "@/app/api/v1/osograph/utils/query-helpers";
import { FilterableConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import {
  NotebookWhereSchema,
  DatasetWhereSchema,
  DataConnectionWhereSchema,
} from "@/app/api/v1/osograph/utils/validation";
import { getOrgScopedClient } from "@/app/api/v1/osograph/utils/access-control";
import {
  buildConnection,
  emptyConnection,
} from "@/app/api/v1/osograph/utils/connection";
import {
  OrganizationsRow,
  UserProfilesRow,
  UsersByOrganizationRow,
} from "@/lib/types/schema-types";

/**
 * Type resolvers for Organization and OrganizationMember.
 * These field resolvers don't require auth checks as they operate on
 * already-fetched organization data.
 */
export const organizationTypeResolvers: GraphQLResolverModule<GraphQLContext> =
  {
    Organization: {
      name: (parent: OrganizationsRow) => parent.org_name,
      displayName: (parent: OrganizationsRow) => parent.org_name,
      createdAt: (parent: OrganizationsRow) => parent.created_at,
      updatedAt: (parent: OrganizationsRow) => parent.updated_at,

      members: async (
        parent: OrganizationsRow,
        args: FilterableConnectionArgs,
        context: GraphQLContext,
      ) => {
        const { client } = await getOrgScopedClient(context, parent.id);

        let query = client
          .from("users_by_organization")
          .select("*, user_profiles(*)", { count: "exact" })
          .eq("org_id", parent.id)
          .is("deleted_at", null);

        if (args.first) {
          query = query.limit(args.first);
        }

        const { data: membersData, count } = await query;

        if (!membersData || membersData.length === 0) {
          return emptyConnection();
        }

        const users = membersData
          .map((m: any) => m.user_profiles)
          .filter(
            (user: UserProfilesRow | null): user is UserProfilesRow =>
              user !== null,
          );

        return buildConnection(users, args, count ?? 0);
      },

      notebooks: async (
        parent: OrganizationsRow,
        args: FilterableConnectionArgs,
        context: GraphQLContext,
      ) => {
        const { client } = await getOrgScopedClient(context, parent.id);

        const options: ExplicitClientQueryOptions<"notebooks"> = {
          client,
          orgIds: [parent.id],
          tableName: "notebooks",
          whereSchema: NotebookWhereSchema,
          basePredicate: {
            is: [{ key: "deleted_at", value: null }],
          },
        };

        return queryWithPagination(args, context, options);
      },

      datasets: async (
        parent: OrganizationsRow,
        args: FilterableConnectionArgs,
        context: GraphQLContext,
      ) => {
        const { client } = await getOrgScopedClient(context, parent.id);

        const options: ExplicitClientQueryOptions<"datasets"> = {
          client,
          orgIds: [parent.id],
          tableName: "datasets",
          whereSchema: DatasetWhereSchema,
          basePredicate: {
            is: [{ key: "deleted_at", value: null }],
          },
        };

        return queryWithPagination(args, context, options);
      },

      dataConnections: async (
        parent: OrganizationsRow,
        args: FilterableConnectionArgs,
        context: GraphQLContext,
      ) => {
        const { client } = await getOrgScopedClient(context, parent.id);

        const options: ExplicitClientQueryOptions<"dynamic_connectors"> = {
          client,
          orgIds: [parent.id],
          tableName: "dynamic_connectors",
          whereSchema: DataConnectionWhereSchema,
          basePredicate: {
            is: [{ key: "deleted_at", value: null }],
          },
        };

        return queryWithPagination(args, context, options);
      },
    },

    OrganizationMember: {
      userId: (parent: UsersByOrganizationRow) => parent.user_id,
      orgId: (parent: UsersByOrganizationRow) => parent.org_id,
      userRole: (parent: UsersByOrganizationRow) =>
        parent.user_role.toUpperCase(),
      createdAt: (parent: UsersByOrganizationRow) => parent.created_at,

      user: async (
        parent: UsersByOrganizationRow,
        _args,
        context: GraphQLContext,
      ) => {
        const { client } = await getOrgScopedClient(context, parent.org_id);
        return getUserProfile(parent.user_id, client);
      },
    },
  };
