import { getOrgResourceClient } from "@/app/api/v1/osograph/utils/access-control";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import {
  getOrganization,
  getUserProfile,
} from "@/app/api/v1/osograph/utils/auth";
import {
  DataIngestionsWhereSchema,
  DataModelWhereSchema,
  RunWhereSchema,
  StaticModelWhereSchema,
  MaterializationWhereSchema,
  DataConnectionAsTableWhereSchema,
} from "@/app/api/v1/osograph/utils/validation";
import type { FilterableConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import { queryWithPagination } from "@/app/api/v1/osograph/utils/query-helpers";
import { assertNever } from "@opensource-observer/utils";
import {
  DataConnectionAsTableRow,
  DataIngestionAsTableRow,
  DatasetsRow,
} from "@/lib/types/schema-types";
import { Connection } from "@/app/api/v1/osograph/utils/connection";
import { getMaterializations } from "@/app/api/v1/osograph/utils/resolver-helpers";
import { generateTableId } from "@/app/api/v1/osograph/utils/model";

/**
 * These types represent intermediate resolver objects for GraphQL union type handling.
 * They're NOT database row types - they're lightweight context carriers created in
 * Dataset.typeDefinition to pass org_id/dataset_id to child resolvers.
 * Inlined here because they're resolver implementation details used only in this file.
 */
type DataModelDefinitionParent = { org_id: string; dataset_id: string };
type StaticModelDefinitionParent = { org_id: string; dataset_id: string };
type DataIngestionDefinitionParent = { org_id: string; dataset_id: string };
type DataConnectionDefinitionParent = { org_id: string; dataset_id: string };

/**
 * Type resolvers for Dataset and related types.
 * These field resolvers don't require auth checks as they operate on
 * already-fetched dataset data.
 */
export const datasetTypeResolvers: GraphQLResolverModule<GraphQLContext> = {
  Dataset: {
    displayName: (parent: DatasetsRow) => parent.display_name,
    createdAt: (parent: DatasetsRow) => parent.created_at,
    updatedAt: (parent: DatasetsRow) => parent.updated_at,
    creatorId: (parent: DatasetsRow) => parent.created_by,
    orgId: (parent: DatasetsRow) => parent.org_id,
    isPublic: (parent: DatasetsRow) => parent.is_public,
    type: (parent: DatasetsRow) => parent.dataset_type,

    creator: async (
      parent: DatasetsRow,
      _args: unknown,
      context: GraphQLContext,
    ) => {
      const { client } = await getOrgResourceClient(
        context,
        "dataset",
        parent.id,
      );
      return getUserProfile(parent.created_by, client);
    },

    organization: async (
      parent: DatasetsRow,
      _args: unknown,
      context: GraphQLContext,
    ) => {
      const { client } = await getOrgResourceClient(
        context,
        "dataset",
        parent.id,
      );
      return getOrganization(parent.org_id, client);
    },

    typeDefinition: async (parent: DatasetsRow) => {
      switch (parent.dataset_type) {
        case "USER_MODEL": {
          return {
            __typename: "DataModelDefinition",
            org_id: parent.org_id,
            dataset_id: parent.id,
          };
        }
        case "STATIC_MODEL":
          return {
            __typename: "StaticModelDefinition",
            org_id: parent.org_id,
            dataset_id: parent.id,
          };
        case "DATA_INGESTION": {
          return {
            __typename: "DataIngestionDefinition",
            org_id: parent.org_id,
            dataset_id: parent.id,
          };
        }
        case "DATA_CONNECTION":
          return {
            __typename: "DataConnectionDefinition",
            org_id: parent.org_id,
            dataset_id: parent.id,
          };
        default:
          assertNever(
            parent.dataset_type,
            `Unknown dataset type: ${parent.dataset_type}`,
          );
      }
    },

    tables: async (
      parent: DatasetsRow,
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      switch (parent.dataset_type) {
        case "USER_MODEL": {
          const { client } = await getOrgResourceClient(
            context,
            "dataset",
            parent.id,
            "read",
          );

          return queryWithPagination(args, context, {
            client,
            orgIds: parent.org_id,
            tableName: "model",
            whereSchema: DataModelWhereSchema,
            basePredicate: {
              is: [{ key: "deleted_at", value: null }],
              eq: [{ key: "dataset_id", value: parent.id }],
            },
          });
        }
        case "STATIC_MODEL": {
          const { client } = await getOrgResourceClient(
            context,
            "dataset",
            parent.id,
            "read",
          );

          return queryWithPagination(args, context, {
            client,
            orgIds: parent.org_id,
            tableName: "static_model",
            whereSchema: StaticModelWhereSchema,
            basePredicate: {
              is: [{ key: "deleted_at", value: null }],
              eq: [{ key: "dataset_id", value: parent.id }],
            },
          });
        }
        case "DATA_INGESTION": {
          const { client } = await getOrgResourceClient(
            context,
            "dataset",
            parent.id,
            "read",
          );

          const result = (await queryWithPagination(args, context, {
            client,
            orgIds: parent.org_id,
            tableName: "data_ingestion_as_table",
            whereSchema: DataIngestionsWhereSchema,
            basePredicate: {
              eq: [{ key: "dataset_id", value: parent.id }],
            },
          })) as Connection<DataIngestionAsTableRow>;

          return {
            ...result,
            edges: result.edges.map((edge) => ({
              node: {
                id: edge.node.table_id,
                name: edge.node.table_name,
                datasetId: edge.node.dataset_id,
              },
              cursor: edge.cursor,
            })),
          };
        }
        case "DATA_CONNECTION": {
          const { client } = await getOrgResourceClient(
            context,
            "dataset",
            parent.id,
            "read",
          );

          const result = (await queryWithPagination(args, context, {
            client,
            orgIds: parent.org_id,
            tableName: "data_connection_as_table",
            whereSchema: DataConnectionAsTableWhereSchema,
            basePredicate: {
              eq: [{ key: "dataset_id", value: parent.id }],
            },
          })) as Connection<DataConnectionAsTableRow>;

          return {
            ...result,
            edges: result.edges.map((edge) => ({
              node: {
                id: edge.node.table_id,
                name: edge.node.table_name,
                datasetId: edge.node.dataset_id,
              },
              cursor: edge.cursor,
            })),
          };
        }
        default:
          assertNever(
            parent.dataset_type,
            `Unknown dataset type: ${parent.dataset_type}`,
          );
      }
    },

    runs: async (
      parent: DatasetsRow,
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      const { client } = await getOrgResourceClient(
        context,
        "dataset",
        parent.id,
      );

      return queryWithPagination(args, context, {
        client,
        orgIds: parent.org_id,
        tableName: "run",
        whereSchema: RunWhereSchema,
        basePredicate: {
          eq: [{ key: "dataset_id", value: parent.id }],
        },
        orderBy: {
          key: "queued_at",
          ascending: false,
        },
      });
    },

    materializations: async (
      parent: DatasetsRow,
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      const { client } = await getOrgResourceClient(
        context,
        "dataset",
        parent.id,
        "read",
      );

      return queryWithPagination(args, context, {
        client,
        orgIds: parent.org_id,
        tableName: "materialization",
        whereSchema: MaterializationWhereSchema,
        basePredicate: {
          eq: [{ key: "dataset_id", value: parent.id }],
        },
        orderBy: {
          key: "created_at",
          ascending: false,
        },
      });
    },
  },

  DataModelDefinition: {
    orgId: (parent: DatasetsRow) => parent.org_id,
    datasetId: (parent: DataModelDefinitionParent) => parent.dataset_id,
    dataModels: async (
      parent: DataModelDefinitionParent,
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      const { client } = await getOrgResourceClient(
        context,
        "dataset",
        parent.dataset_id,
        "read",
      );

      return queryWithPagination(args, context, {
        client,
        orgIds: parent.org_id,
        tableName: "model",
        whereSchema: DataModelWhereSchema,
        basePredicate: {
          is: [{ key: "deleted_at", value: null }],
          eq: [{ key: "dataset_id", value: parent.dataset_id }],
        },
      });
    },
  },

  StaticModelDefinition: {
    orgId: (parent: StaticModelDefinitionParent) => parent.org_id,
    datasetId: (parent: StaticModelDefinitionParent) => parent.dataset_id,
    staticModels: async (
      parent: StaticModelDefinitionParent,
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      const { client } = await getOrgResourceClient(
        context,
        "dataset",
        parent.dataset_id,
        "read",
      );

      return queryWithPagination(args, context, {
        client,
        orgIds: parent.org_id,
        tableName: "static_model",
        whereSchema: StaticModelWhereSchema,
        basePredicate: {
          is: [{ key: "deleted_at", value: null }],
          eq: [{ key: "dataset_id", value: parent.dataset_id }],
        },
      });
    },
  },

  DataIngestionDefinition: {
    orgId: (parent: DataIngestionDefinitionParent) => parent.org_id,
    datasetId: (parent: DataIngestionDefinitionParent) => parent.dataset_id,
    dataIngestion: async (
      parent: DataIngestionDefinitionParent,
      _args: Record<string, never>,
      context: GraphQLContext,
    ) => {
      const { client } = await getOrgResourceClient(
        context,
        "dataset",
        parent.dataset_id,
      );

      const { data: config } = await client
        .from("data_ingestions")
        .select("*")
        .eq("dataset_id", parent.dataset_id)
        .is("deleted_at", null)
        .maybeSingle();

      return config;
    },
    materializations: async (
      parent: DataIngestionDefinitionParent,
      args: FilterableConnectionArgs & { tableName: string },
      context: GraphQLContext,
    ) => {
      const { tableName, ...restArgs } = args;
      return getMaterializations(
        restArgs,
        context,
        parent.org_id,
        parent.dataset_id,
        generateTableId("DATA_INGESTION", tableName),
      );
    },
  },

  DataConnectionDefinition: {
    orgId: (parent: DataConnectionDefinitionParent) => parent.org_id,
    datasetId: (parent: DataConnectionDefinitionParent) => parent.dataset_id,
    dataConnectionAlias: async (
      parent: DataConnectionDefinitionParent,
      _args: Record<string, never>,
      context: GraphQLContext,
    ) => {
      const { client } = await getOrgResourceClient(
        context,
        "dataset",
        parent.dataset_id,
      );

      const { data: alias } = await client
        .from("data_connection_alias")
        .select("*")
        .eq("dataset_id", parent.dataset_id)
        .is("deleted_at", null)
        .maybeSingle();

      return alias;
    },
  },
};
