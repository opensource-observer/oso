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
  DatasetWhereSchema,
  DataModelWhereSchema,
  TableMetadataWhereSchema,
} from "@/app/api/v1/osograph/utils/validation";
import {
  ResourceErrors,
  ServerErrors,
} from "@/app/api/v1/osograph/utils/errors";
import type {
  ConnectionArgs,
  FilterableConnectionArgs,
} from "@/app/api/v1/osograph/utils/pagination";
import {
  getUserOrganizationIds,
  requireOrganizationAccess,
  buildConnectionOrEmpty,
  preparePaginationRange,
} from "@/app/api/v1/osograph/utils/resolver-helpers";
import { emptyConnection } from "@/app/api/v1/osograph/utils/connection";
import { Column, ColumnSchema } from "@/lib/types/catalog";
import z from "zod";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import { getDataModelsConnection } from "@/app/api/v1/osograph/schema/resolvers/data-model";
import {
  buildQuery,
  mergePredicates,
  type QueryPredicate,
} from "@/app/api/v1/osograph/utils/query-builder";
import { parseWhereClause } from "@/app/api/v1/osograph/utils/where-parser";

export async function getDatasetsConnection(
  orgIds: string | string[],
  args: ConnectionArgs,
  additionalPredicate?: Partial<QueryPredicate<"datasets">>,
) {
  const supabase = createAdminClient();
  const orgIdArray = Array.isArray(orgIds) ? orgIds : [orgIds];

  if (orgIdArray.length === 0) {
    return emptyConnection();
  }

  const [start, end] = preparePaginationRange(args);

  const basePredicate: Partial<QueryPredicate<"datasets">> = {
    in: [{ key: "org_id", value: orgIdArray }],
    is: [{ key: "deleted_at", value: null }],
  };

  const predicate = additionalPredicate
    ? mergePredicates(basePredicate, additionalPredicate)
    : basePredicate;

  const {
    data: datasets,
    count,
    error,
  } = await buildQuery(supabase, "datasets", predicate, (query) =>
    query.range(start, end),
  );

  if (error) {
    throw ServerErrors.database(`Failed to fetch datasets: ${error.message}`);
  }

  return buildConnectionOrEmpty(datasets, args, count);
}

export const datasetResolvers: GraphQLResolverModule<GraphQLContext> = {
  Query: {
    datasets: async (
      _: unknown,
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);

      const orgIds = await getUserOrganizationIds(authenticatedUser.userId);
      if (orgIds.length === 0) {
        return buildConnectionOrEmpty(null, args, 0);
      }

      const validatedWhere = args.where
        ? validateInput(DatasetWhereSchema, args.where)
        : undefined;

      return getDatasetsConnection(
        orgIds,
        args,
        validatedWhere ? parseWhereClause(validatedWhere) : undefined,
      );
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

    dataModels: async (
      parent: { id: string; org_id: string },
      args: FilterableConnectionArgs,
    ) => {
      const validatedWhere = args.where
        ? validateInput(DataModelWhereSchema, args.where)
        : undefined;

      return getDataModelsConnection(
        [parent.org_id],
        {
          ...args,
          datasetId: parent.id,
        },
        validatedWhere ? parseWhereClause(validatedWhere) : undefined,
      );
    },
  },
};
