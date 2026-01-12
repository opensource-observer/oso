import { v4 as uuidv4 } from "uuid";
import { createAdminClient } from "@/lib/supabase/admin";
import { signTrinoJWT } from "@/lib/auth/auth";
import { getTrinoClient } from "@/lib/clients/trino";
import { logger } from "@/lib/logger";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import {
  getOrganization,
  getUserProfile,
  requireAuthentication,
  requireOrgMembership,
} from "@/app/api/v1/osograph/utils/auth";
import {
  CreateDatasetSchema,
  DataModelWhereSchema,
  DatasetWhereSchema,
  RunWhereSchema,
  StaticModelWhereSchema,
  TableMetadataWhereSchema,
  UpdateDatasetSchema,
  validateInput,
} from "@/app/api/v1/osograph/utils/validation";
import {
  DatasetErrors,
  ServerErrors,
} from "@/app/api/v1/osograph/utils/errors";
import type { FilterableConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import { requireOrganizationAccess } from "@/app/api/v1/osograph/utils/resolver-helpers";
import { Column, ColumnSchema } from "@/lib/types/catalog";
import z from "zod";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import { queryWithPagination } from "@/app/api/v1/osograph/utils/query-helpers";
import { assertNever } from "@opensource-observer/utils";
import { DatasetsRow } from "@/lib/types/schema-types";

export const datasetResolvers: GraphQLResolverModule<GraphQLContext> = {
  Query: {
    datasets: async (
      _: unknown,
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      return queryWithPagination(args, context, {
        tableName: "datasets",
        whereSchema: DatasetWhereSchema,
        requireAuth: true,
        filterByUserOrgs: true,
        basePredicate: {
          is: [{ key: "deleted_at", value: null }],
        },
      });
    },

    tables: async (
      _: unknown,
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const validatedWhere = validateInput(
        TableMetadataWhereSchema,
        args.where,
      );

      const { orgId, catalogName, schemaName, tableName } = {
        orgId: validatedWhere.orgId.eq,
        catalogName: validatedWhere.catalogName.eq,
        schemaName: validatedWhere.schemaName.eq,
        tableName: validatedWhere.tableName.eq,
      };

      const org = await requireOrganizationAccess(
        authenticatedUser.userId,
        orgId,
      );

      const trinoJwt = await signTrinoJWT({
        ...authenticatedUser,
        orgId: org.id,
        orgName: org.org_name,
        orgRole: "member",
      });

      const trino = getTrinoClient(trinoJwt);

      const query = `
        SELECT column_name, data_type, column_comment
        FROM ${catalogName}.information_schema.columns
        WHERE table_schema = '${schemaName}' AND table_name = '${tableName}'
      `;
      const { data: columnResult, error } = await trino.queryAll(query);
      if (error || !columnResult) {
        logger.error(
          `Failed to fetch table metadata for user ${authenticatedUser.userId}:`,
          error.message,
        );
        throw ServerErrors.externalService("Failed to fetch table metadata");
      }

      const results = await Promise.all(
        columnResult
          .flatMap((column) => column.data)
          .map(
            async (
              column: (string | null)[] | undefined,
            ): Promise<Column | null> => {
              if (!column || column.length !== 3) {
                return null;
              }
              const [columnName, columnType, columnComment] = column;
              return ColumnSchema.parse({
                name: columnName,
                type: columnType,
                description: columnComment ?? null,
              });
            },
          ),
      );
      const filteredResults = results.filter((result) => result !== null);
      return filteredResults;
    },
  },

  Mutation: {
    createDataset: async (
      _: unknown,
      { input }: { input: z.infer<typeof CreateDatasetSchema> },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const validated = validateInput(CreateDatasetSchema, input);
      const organization = await getOrganization(validated.orgId);
      await requireOrgMembership(authenticatedUser.userId, organization.id);

      const supabase = createAdminClient();
      const datasetId = uuidv4();

      const { data: dataset, error } = await supabase
        .from("datasets")
        .insert({
          id: datasetId,
          org_id: organization.id,
          name: validated.name,
          display_name: validated.displayName,
          description: validated.description,
          created_by: authenticatedUser.userId,
          is_public: validated.isPublic ?? false,
          dataset_type: validated.type,
        })
        .select()
        .single();

      if (error) {
        logger.error("Failed to create dataset:", error);
        throw ServerErrors.database("Failed to create dataset");
      }

      return {
        dataset,
        message: "Dataset created successfully",
        success: true,
      };
    },

    updateDataset: async (
      _: unknown,
      args: {
        input: {
          id: string;
          name?: string;
          displayName?: string;
          description?: string;
          isPublic?: boolean;
        };
      },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const input = validateInput(UpdateDatasetSchema, args.input);

      const supabase = createAdminClient();

      const { data: existingDataset, error: existingError } = await supabase
        .from("datasets")
        .select("org_id")
        .eq("id", input.id)
        .single();

      if (existingError || !existingDataset) {
        throw DatasetErrors.notFound();
      }

      await requireOrgMembership(
        authenticatedUser.userId,
        existingDataset.org_id,
      );

      const { data, error } = await supabase
        .from("datasets")
        .update({
          name: input.name,
          display_name: input.displayName,
          description: input.description,
          is_public: input.isPublic,
        })
        .eq("id", input.id)
        .select()
        .single();

      if (error) {
        throw ServerErrors.database(
          `Failed to update dataset: ${error.message}`,
        );
      }

      return {
        dataset: data,
        message: "Dataset updated successfully",
        success: true,
      };
    },
  },

  Dataset: {
    displayName: (parent: { display_name: string | null }) =>
      parent.display_name,
    createdAt: (parent: { created_at: string }) => parent.created_at,
    updatedAt: (parent: { updated_at: string }) => parent.updated_at,
    creatorId: (parent: { created_by: string }) => parent.created_by,
    orgId: (parent: { org_id: string }) => parent.org_id,
    isPublic: (parent: { is_public: boolean }) => parent.is_public,
    type: (parent: { dataset_type: string }) => parent.dataset_type,

    creator: async (parent: { created_by: string }) => {
      return getUserProfile(parent.created_by);
    },

    organization: async (parent: { org_id: string }) => {
      return getOrganization(parent.org_id);
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
        case "DATA_CONNECTOR":
          throw new Error(
            `Dataset type "${parent.dataset_type}" is not supported yet.`,
          );
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
          return queryWithPagination(args, context, {
            tableName: "model",
            whereSchema: DataModelWhereSchema,
            requireAuth: false,
            filterByUserOrgs: false,
            parentOrgIds: parent.org_id,
            basePredicate: {
              is: [{ key: "deleted_at", value: null }],
              eq: [{ key: "dataset_id", value: parent.id }],
            },
          });
        }
        case "STATIC_MODEL":
          return queryWithPagination(args, context, {
            tableName: "static_model",
            whereSchema: StaticModelWhereSchema,
            requireAuth: false,
            filterByUserOrgs: false,
            parentOrgIds: parent.org_id,
            basePredicate: {
              is: [{ key: "deleted_at", value: null }],
              eq: [{ key: "dataset_id", value: parent.id }],
            },
          });
        case "DATA_INGESTION": {
          return queryWithPagination(args, context, {
            tableName: "data_ingestions",
            whereSchema: DatasetWhereSchema,
            requireAuth: false,
            filterByUserOrgs: false,
            parentOrgIds: parent.org_id,
            basePredicate: {
              eq: [{ key: "dataset_id", value: parent.id }],
            },
          });
        }
        case "DATA_CONNECTOR":
          // Table metadata is not available until after the ingestion job completes
          // Tables are created dynamically during ingestion
          return {
            edges: [],
            pageInfo: {
              hasNextPage: false,
              hasPreviousPage: false,
              startCursor: null,
              endCursor: null,
            },
            totalCount: 0,
          };
        default:
          assertNever(
            parent.dataset_type,
            `Unknown dataset type: ${parent.dataset_type}`,
          );
      }
    },

    runs: async (
      parent: { id: string; org_id: string },
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      return queryWithPagination(args, context, {
        tableName: "run",
        whereSchema: RunWhereSchema,
        requireAuth: false,
        filterByUserOrgs: false,
        parentOrgIds: parent.org_id,
        basePredicate: {
          eq: [{ key: "dataset_id", value: parent.id }],
        },
        orderBy: {
          key: "started_at",
          ascending: false,
        },
      });
    },
  },

  DataModelDefinition: {
    orgId: (parent: { org_id: string }) => parent.org_id,
    datasetId: (parent: { dataset_id: string }) => parent.dataset_id,
    dataModels: async (
      parent: { dataset_id: string; org_id: string },
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      return queryWithPagination(args, context, {
        tableName: "model",
        whereSchema: DataModelWhereSchema,
        requireAuth: false,
        filterByUserOrgs: false,
        parentOrgIds: parent.org_id,
        basePredicate: {
          is: [{ key: "deleted_at", value: null }],
          eq: [{ key: "dataset_id", value: parent.dataset_id }],
        },
      });
    },
  },

  StaticModelDefinition: {
    orgId: (parent: { org_id: string }) => parent.org_id,
    datasetId: (parent: { dataset_id: string }) => parent.dataset_id,
    staticModels: async (
      parent: { dataset_id: string; org_id: string },
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      return queryWithPagination(args, context, {
        tableName: "static_model",
        whereSchema: StaticModelWhereSchema,
        requireAuth: false,
        filterByUserOrgs: false,
        parentOrgIds: parent.org_id,
        basePredicate: {
          is: [{ key: "deleted_at", value: null }],
          eq: [{ key: "dataset_id", value: parent.dataset_id }],
        },
      });
    },
  },
};
