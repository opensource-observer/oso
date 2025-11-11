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
  validateInput,
  CreateDatasetSchema,
  UpdateDatasetSchema,
} from "@/app/api/v1/osograph/utils/validation";
import {
  ResourceErrors,
  ServerErrors,
} from "@/app/api/v1/osograph/utils/errors";
import type { ConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import {
  getUserOrganizationIds,
  requireOrganizationAccess,
  getResourceById,
  buildConnectionOrEmpty,
  preparePaginationRange,
} from "@/app/api/v1/osograph/utils/resolver-helpers";
import {
  emptyConnection,
  type Connection,
} from "@/app/api/v1/osograph/utils/connection";
import { Column, ColumnSchema } from "@/lib/types/catalog";
import z from "zod";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import { getModelsConnection } from "@/app/api/v1/osograph/schema/resolvers/model";

export async function getRawDatasets(
  orgIds: string[],
  args: ConnectionArgs,
): Promise<{ data: any[] | null; count: number | null }> {
  const supabase = createAdminClient();
  const [start, end] = preparePaginationRange(args);

  const query = supabase
    .from("datasets")
    .select("*", { count: "exact" })
    .is("deleted_at", null)
    .range(start, end);

  const { data: datasets, count } =
    orgIds.length === 1
      ? await query.eq("org_id", orgIds[0])
      : await query.in("org_id", orgIds);

  return { data: datasets, count };
}

export async function getDatasetsConnection(
  orgIds: string | string[],
  args: ConnectionArgs,
): Promise<Connection<any>> {
  const orgIdArray = Array.isArray(orgIds) ? orgIds : [orgIds];

  if (orgIdArray.length === 0) {
    return emptyConnection();
  }

  const { data: datasets, count } = await getRawDatasets(orgIdArray, args);
  return buildConnectionOrEmpty(datasets, args, count);
}

export const datasetResolvers: GraphQLResolverModule<GraphQLContext> = {
  Query: {
    datasets: async (
      _: unknown,
      args: ConnectionArgs,
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);

      const orgIds = await getUserOrganizationIds(authenticatedUser.userId);
      if (orgIds.length === 0) {
        return buildConnectionOrEmpty(null, args, 0);
      }

      return getDatasetsConnection(orgIds, args);
    },

    dataset: async (
      _: unknown,
      args: { id: string },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      return getResourceById({
        tableName: "datasets",
        id: args.id,
        userId: authenticatedUser.userId,
        checkMembership: true,
      });
    },

    datasetTableMetadata: async (
      _: unknown,
      args: {
        orgId: string;
        catalogName: string;
        schemaName: string;
        tableName: string;
      },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const org = await requireOrganizationAccess(
        authenticatedUser.userId,
        args.orgId,
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
        FROM ${args.catalogName}.information_schema.columns
        WHERE table_schema = '${args.schemaName}' AND table_name = '${args.tableName}'
      `;
      const { data: columnResult, error } = await trino.queryAll(query);
      if (error || !columnResult) {
        logger.error(
          `Failed to fetch catalogs for user ${authenticatedUser.userId}:`,
          error.message,
        );
        throw ServerErrors.externalService("Failed to fetch catalogs");
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
      let catalog: string;
      let schema: string;

      switch (validated.type) {
        case "USER_MODEL":
          catalog = "user_iceberg";
          schema = `ds_${datasetId.replace(/-/g, "")}`;
          break;
        default:
          throw new Error(
            `Dataset type "${validated.type}" is not supported yet.`,
          );
      }

      const { data: dataset, error } = await supabase
        .from("datasets")
        .insert({
          id: datasetId,
          org_id: organization.id,
          name: validated.name,
          display_name: validated.displayName,
          description: validated.description,
          catalog,
          schema,
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
        throw ResourceErrors.notFound("Dataset", input.id);
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

    models: async (
      parent: { id: string; org_id: string },
      args: ConnectionArgs,
    ) => {
      return getModelsConnection([parent.org_id], {
        ...args,
        datasetId: parent.id,
      });
    },
  },
};
