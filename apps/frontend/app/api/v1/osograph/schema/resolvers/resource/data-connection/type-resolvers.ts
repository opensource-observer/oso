import { getOrganization } from "@/app/api/v1/osograph/utils/auth";
import {
  DynamicConnectorsRow,
  DataConnectionAliasRow,
} from "@/lib/types/schema-types";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import type { FilterableConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import { getMaterializations } from "@/app/api/v1/osograph/utils/resolver-helpers";
import { generateTableId } from "@/app/api/v1/osograph/utils/model";
import { getOrgResourceClient } from "@/app/api/v1/osograph/utils/access-control";

/**
 * Type resolvers for DataConnection and DataConnectionAlias.
 * These field resolvers don't require auth checks as they operate on
 * already-fetched data connection data.
 */
export const dataConnectionTypeResolvers: GraphQLResolverModule<GraphQLContext> =
  {
    DataConnection: {
      orgId: (parent: DynamicConnectorsRow) => parent.org_id,
      createdAt: (parent: DynamicConnectorsRow) => parent.created_at,
      updatedAt: (parent: DynamicConnectorsRow) => parent.updated_at,
      organization: async (
        parent: DynamicConnectorsRow,
        _args: unknown,
        context: GraphQLContext,
      ) => {
        const { client } = await getOrgResourceClient(
          context,
          "data_connection",
          parent.id,
          "read",
        );
        return getOrganization(parent.org_id, client);
      },
      name: (parent: DynamicConnectorsRow) => parent.connector_name,
      type: (parent: DynamicConnectorsRow) =>
        parent.connector_type.toUpperCase(),
    },

    DataConnectionAlias: {
      orgId: (parent: DataConnectionAliasRow) => parent.org_id,
      datasetId: (parent: DataConnectionAliasRow) => parent.dataset_id,
      dataConnectionId: (parent: DataConnectionAliasRow) =>
        parent.data_connection_id,
      schema: (parent: DataConnectionAliasRow) => parent.schema_name,
      createdAt: (parent: DataConnectionAliasRow) => parent.created_at,
      updatedAt: (parent: DataConnectionAliasRow) => parent.updated_at,
      materializations: async (
        parent: DataConnectionAliasRow,
        args: FilterableConnectionArgs & { tableName: string },
        context: GraphQLContext,
      ) => {
        const { tableName, ...restArgs } = args;
        return getMaterializations(
          restArgs,
          context,
          parent.org_id,
          parent.dataset_id,
          generateTableId("DATA_CONNECTION", tableName),
        );
      },
    },
  };
