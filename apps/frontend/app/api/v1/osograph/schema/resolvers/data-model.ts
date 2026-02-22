import { createAdminClient } from "@/lib/supabase/admin";
import { logger } from "@/lib/logger";
import { getOrganization } from "@/app/api/v1/osograph/utils/auth";
import {
  ResourceErrors,
  ServerErrors,
} from "@/app/api/v1/osograph/utils/errors";
import {
  getMaterializations,
  getModelRunConnection,
  getResourceById,
} from "@/app/api/v1/osograph/utils/resolver-helpers";
import { queryWithPagination } from "@/app/api/v1/osograph/utils/query-helpers";
import { ModelUpdate } from "@/lib/types/schema-types";
import { getModelContext } from "@/app/api/v1/osograph/schema/resolvers/model-context";
import {
  executePreviewQuery,
  generateTableId,
} from "@/app/api/v1/osograph/utils/model";
import {
  DataModelReleaseWhereSchema,
  DataModelRevisionWhereSchema,
  DataModelWhereSchema,
} from "@/app/api/v1/osograph/utils/validation";
import { z } from "zod";
import {
  MutationResolvers,
  QueryResolvers,
  DataModelResolvers,
  DataModelRevisionResolvers as DataModelRevisionFieldResolvers,
  DataModelReleaseResolvers as DataModelReleaseFieldResolvers,
} from "@/app/api/v1/osograph/types/generated/types";
import {
  createResolver,
  createResolversCollection,
  ResolverBuilder,
} from "@/app/api/v1/osograph/utils/resolver-builder";
import {
  withOrgScopedClient,
  withOrgResourceClient,
  withAuthenticatedClient,
  withValidation,
} from "@/app/api/v1/osograph/utils/resolver-middleware";
import {
  CreateDataModelInputSchema,
  CreateDataModelReleaseInputSchema,
  CreateDataModelRevisionInputSchema,
  UpdateDataModelInputSchema,
} from "@/app/api/v1/osograph/types/generated/validation";
import { createHash } from "crypto";

type DataModelQueryResolvers = Pick<QueryResolvers, "dataModels">;
type DataModelMutationResolvers = Pick<
  Required<MutationResolvers>,
  | "createDataModel"
  | "updateDataModel"
  | "createDataModelRevision"
  | "createDataModelRelease"
  | "deleteDataModel"
>;

type DataModelRelatedResolvers = {
  Query: DataModelQueryResolvers;
  Mutation: DataModelMutationResolvers;
  DataModel: DataModelResolvers;
  DataModelRevision: DataModelRevisionFieldResolvers;
  DataModelRelease: DataModelReleaseFieldResolvers;
};

/**
 * Common middleware for mutations that operate on an existing DataModel.
 *
 * @param builder - The resolver builder to apply middleware to
 * @param schema - The Zod schema for validating the input
 * @param getExistingModelId - A function that extracts the existing DataModel ID from the input for authorization checks
 * @returns The resolver builder with validation and authorization middleware applied
 */
function existingDataModelMiddleware<TSchema extends z.ZodSchema>(
  builder: ResolverBuilder<any, any, any, any>,
  schema: TSchema,
  getExistingModelId: (input: z.infer<TSchema>) => string,
) {
  return builder
    .use(withValidation(schema))
    .use(
      withOrgResourceClient(
        "data_model",
        ({ args }) => getExistingModelId(args.input),
        "write",
      ),
    );
}

const mutations = createResolversCollection<DataModelMutationResolvers>()
  .defineWithBuilder("createDataModel", (builder) => {
    return builder
      .use(withValidation(CreateDataModelInputSchema()))
      .use(withOrgScopedClient(({ args }) => args.input.orgId))
      .resolve(async (_, { input }, context) => {
        const { data, error } = await context.client
          .from("model")
          .insert({
            org_id: input.orgId,
            dataset_id: input.datasetId,
            name: input.name,
            is_enabled: input.isEnabled ?? true,
          })
          .select()
          .single();

        if (error) {
          logger.error("Failed to create dataModel:", error);
          throw ServerErrors.database("Failed to create dataModel");
        }
        return {
          success: true,
          message: "DataModel created successfully",
          dataModel: data,
        };
      });
  })
  .defineWithBuilder("updateDataModel", (builder) => {
    return existingDataModelMiddleware(
      builder,
      UpdateDataModelInputSchema(),
      (input) => input.dataModelId,
    ).resolve(async (_, { input }, context) => {
      const updateData: ModelUpdate = {};
      if (input.name) {
        updateData.name = input.name;
      }
      if (input.isEnabled !== undefined && input.isEnabled !== null) {
        updateData.is_enabled = input.isEnabled;
      }
      if (Object.keys(updateData).length > 0) {
        updateData.updated_at = new Date().toISOString();
      }

      const { data, error } = await context.client
        .from("model")
        .update(updateData)
        .eq("id", input.dataModelId)
        .select()
        .single();

      if (error) {
        logger.error("Failed to update dataModel:", error);
        throw ServerErrors.database("Failed to update dataModel");
      }

      return {
        success: true,
        message: "DataModel updated successfully",
        dataModel: data,
      };
    });
  })
  .defineWithBuilder("createDataModelRevision", (builder) => {
    return existingDataModelMiddleware(
      builder,
      CreateDataModelRevisionInputSchema(),
      (input) => input.dataModelId,
    ).resolve(async (_, { input }, context) => {
      const { data: dataModel, error: dataModelError } = await context.client
        .from("model")
        .select("org_id")
        .eq("id", input.dataModelId)
        .single();

      if (dataModelError || !dataModel) {
        throw ResourceErrors.notFound("DataModel", input.dataModelId);
      }

      const { data: latestRevision } = await context.client
        .from("model_revision")
        .select("*")
        .eq("model_id", input.dataModelId)
        .order("revision_number", { ascending: false })
        .limit(1)
        .single();

      const hash = createHash("sha256")
        .update(
          JSON.stringify(
            Object.entries(input).sort((a, b) => a[0].localeCompare(b[0])),
          ),
        )
        .digest("hex");

      if (latestRevision?.hash === hash) {
        return {
          success: true,
          message: "No changes detected, returning existing revision",
          dataModelRevision: latestRevision,
        };
      }

      const revisionNumber = (latestRevision?.revision_number || 0) + 1;

      const { data, error } = await context.client
        .from("model_revision")
        .insert({
          org_id: dataModel.org_id,
          model_id: input.dataModelId,
          name: input.name,
          description: input.description,
          revision_number: revisionNumber,
          hash,
          language: input.language,
          code: input.code,
          cron: input.cron,
          start: input.start,
          end: input.end,
          schema: input.schema.map((col) => ({
            name: col.name,
            type: col.type,
            description: col.description ?? null,
          })),
          depends_on: input.dependsOn?.map((d) => ({
            model_id: d.dataModelId,
            alias: d.alias ?? null,
          })),
          partitioned_by: input.partitionedBy,
          clustered_by: input.clusteredBy,
          kind: input.kind,
          kind_options: input.kindOptions
            ? {
                time_column: input.kindOptions.timeColumn ?? null,
                time_column_format: input.kindOptions.timeColumnFormat ?? null,
                batch_size: input.kindOptions.batchSize ?? null,
                lookback: input.kindOptions.lookback ?? null,
                unique_key_columns: input.kindOptions.uniqueKeyColumns ?? null,
                when_matched_sql: input.kindOptions.whenMatchedSql ?? null,
                merge_filter: input.kindOptions.mergeFilter ?? null,
                valid_from_name: input.kindOptions.validFromName ?? null,
                valid_to_name: input.kindOptions.validToName ?? null,
                invalidate_hard_deletes:
                  input.kindOptions.invalidateHardDeletes ?? null,
                updated_at_column: input.kindOptions.updatedAtColumn ?? null,
                updated_at_as_valid_from:
                  input.kindOptions.updatedAtAsValidFrom ?? null,
                scd_columns: input.kindOptions.scdColumns ?? null,
                execution_time_as_valid_from:
                  input.kindOptions.executionTimeAsValidFrom ?? null,
              }
            : null,
        })
        .select()
        .single();

      if (error) {
        logger.error("Failed to create dataModel revision:", error);
        throw ServerErrors.database("Failed to create dataModel revision");
      }

      return {
        success: true,
        message: "DataModel revision created successfully",
        dataModelRevision: data,
      };
    });
  })
  .defineWithBuilder("createDataModelRelease", (builder) => {
    return existingDataModelMiddleware(
      builder,
      CreateDataModelReleaseInputSchema(),
      (input) => input.dataModelId,
    ).resolve(async (_, { input }, context) => {
      const { data: dataModel, error: dataModelError } = await context.client
        .from("model")
        .select("org_id")
        .eq("id", input.dataModelId)
        .single();

      if (dataModelError || !dataModel) {
        throw ResourceErrors.notFound("DataModel", input.dataModelId);
      }

      const { error: revisionError } = await context.client
        .from("model_revision")
        .select("id")
        .eq("id", input.dataModelRevisionId)
        .eq("model_id", input.dataModelId)
        .single();

      if (revisionError) {
        throw ResourceErrors.notFound(
          "DataModelRevision",
          input.dataModelRevisionId,
        );
      }

      const { data, error } = await context.client
        .from("model_release")
        .upsert({
          org_id: dataModel.org_id,
          model_id: input.dataModelId,
          model_revision_id: input.dataModelRevisionId,
          description: input.description,
        })
        .select()
        .single();

      if (error) {
        logger.error("Failed to create dataModel release:", error);
        throw ServerErrors.database("Failed to create dataModel release");
      }

      return {
        success: true,
        message: "DataModel release created successfully",
        dataModelRelease: data,
      };
    });
  })
  .defineWithBuilder("deleteDataModel", (builder) => {
    return builder
      .use(withOrgResourceClient("data_model", ({ args }) => args.id, "admin"))
      .resolve(async (_, { id }, context) => {
        const { error } = await context.client
          .from("model")
          .update({ deleted_at: new Date().toISOString() })
          .eq("id", id);

        if (error) {
          throw ServerErrors.database(
            `Failed to delete data model: ${error.message}`,
          );
        }

        return {
          success: true,
          message: "DataModel deleted successfully",
        };
      });
  })
  .resolvers();

/**
 * QUERY RESOLVERS:
 *
 * Strongly typed query resolvers using queryWithPagination utility.
 */
const queries: DataModelQueryResolvers = {
  dataModels: async (_, args, context) => {
    return queryWithPagination(args, context, {
      tableName: "model",
      whereSchema: DataModelWhereSchema,
      requireAuth: true,
      filterByUserOrgs: true,
      basePredicate: {
        is: [{ key: "deleted_at", value: null }],
      },
    });
  },
};

/**
 * FIELD RESOLVERS:
 *
 * Type resolvers for DataModel, DataModelRevision, and DataModelRelease.
 */
const dataModelTypeResolvers: Pick<
  DataModelRelatedResolvers,
  "DataModel" | "DataModelRevision" | "DataModelRelease"
> = {
  DataModel: {
    id: (parent) => parent.id,
    name: (parent) => parent.name,
    orgId: (parent) => parent.org_id,
    organization: (parent) => getOrganization(parent.org_id),
    dataset: async (parent) => {
      const dataset = await getResourceById({
        tableName: "datasets",
        id: parent.dataset_id,
        userId: "",
      });
      if (!dataset) {
        throw ResourceErrors.notFound("Dataset", parent.dataset_id);
      }
      return dataset as any; // Type narrowing workaround
    },
    revisions: async (parent, args, context) => {
      return queryWithPagination(args, context, {
        tableName: "model_revision",
        whereSchema: DataModelRevisionWhereSchema,
        requireAuth: false,
        filterByUserOrgs: false,
        parentOrgIds: parent.org_id,
        basePredicate: {
          eq: [{ key: "model_id", value: parent.id }],
        },
      });
    },
    releases: async (parent, args, context) => {
      return queryWithPagination(args, context, {
        tableName: "model_release",
        whereSchema: DataModelReleaseWhereSchema,
        requireAuth: false,
        filterByUserOrgs: false,
        parentOrgIds: parent.org_id,
        basePredicate: {
          eq: [{ key: "model_id", value: parent.id }],
        },
        orderBy: {
          key: "created_at",
          ascending: false,
        },
      });
    },
    isEnabled: (parent) => parent.is_enabled,
    createdAt: (parent) => parent.created_at,
    updatedAt: (parent) => parent.updated_at,
    latestRevision: async (parent) => {
      const supabase = createAdminClient();
      const { data, error } = await supabase
        .from("model_revision")
        .select("*")
        .eq("model_id", parent.id)
        .order("revision_number", { ascending: false })
        .limit(1)
        .single();

      if (error) {
        return null;
      }
      return data;
    },
    latestRelease: async (parent) => {
      const supabase = createAdminClient();
      const { data, error } = await supabase
        .from("model_release")
        .select("*")
        .eq("model_id", parent.id)
        .order("created_at", { ascending: false })
        .limit(1)
        .single();

      if (error) {
        return null;
      }
      return data;
    },
    runs: async (parent, args) => {
      return getModelRunConnection(parent.dataset_id, parent.id, args);
    },
    modelContext: async (parent) => {
      return getModelContext(parent.dataset_id, parent.id);
    },
    materializations: async (parent, args, context) => {
      return getMaterializations(
        args,
        context,
        parent.org_id,
        parent.dataset_id,
        generateTableId("USER_MODEL", parent.id),
      );
    },
    previewData: createResolver<DataModelResolvers, "previewData">()
      .use(withAuthenticatedClient())
      .resolve(async (parent, _args, context) => {
        const tableId = generateTableId("USER_MODEL", parent.id);

        return executePreviewQuery(
          parent.org_id,
          parent.dataset_id,
          tableId,
          context.authenticatedUser,
          parent.name,
        );
      }),
  },

  DataModelRevision: {
    id: (parent) => parent.id,
    name: (parent) => parent.name,
    description: (parent) => parent.description,
    code: (parent) => parent.code,
    hash: (parent) => parent.hash,
    language: (parent) => parent.language,
    cron: (parent) => parent.cron,
    kind: (parent) => parent.kind,
    schema: (parent) =>
      parent.schema.map((col) => ({
        name: col.name ?? "",
        type: col.type ?? "",
        description: col.description,
      })),
    orgId: (parent) => parent.org_id,
    dataModelId: (parent) => parent.model_id,
    dataModel: async (parent) => {
      const supabase = createAdminClient();
      const { data, error } = await supabase
        .from("model")
        .select("*")
        .eq("id", parent.model_id)
        .single();
      if (error) {
        throw ResourceErrors.notFound("DataModel", parent.model_id);
      }
      return data;
    },
    organization: (parent) => getOrganization(parent.org_id),
    revisionNumber: (parent) => parent.revision_number,
    start: (parent) => (parent.start ? parent.start : null),
    end: (parent) => (parent.end ? parent.end : null),
    dependsOn: (parent) =>
      parent.depends_on?.map((dep) => ({
        dataModelId: dep.model_id ?? "",
        tableId: dep.model_id ?? "",
        alias: dep.alias,
      })) ?? null,
    partitionedBy: (parent) => parent.partitioned_by ?? null,
    clusteredBy: (parent) => parent.clustered_by ?? null,
    kindOptions: (parent) => parent.kind_options ?? null,
    createdAt: (parent) => parent.created_at,
  },

  DataModelRelease: {
    id: (parent) => parent.id,
    description: (parent) => parent.description,
    orgId: (parent) => parent.org_id,
    dataModelId: (parent) => parent.model_id,
    revisionId: (parent) => parent.model_revision_id,
    dataModel: async (parent) => {
      const supabase = createAdminClient();
      const { data, error } = await supabase
        .from("model")
        .select("*")
        .eq("id", parent.model_id)
        .single();
      if (error) {
        throw ResourceErrors.notFound("DataModel", parent.model_id);
      }
      return data;
    },
    revision: async (parent) => {
      const supabase = createAdminClient();
      const { data, error } = await supabase
        .from("model_revision")
        .select("*")
        .eq("id", parent.model_revision_id)
        .single();
      if (error) {
        throw ResourceErrors.notFound(
          "DataModelRevision",
          parent.model_revision_id,
        );
      }
      return data;
    },
    organization: (parent) => getOrganization(parent.org_id),
    createdAt: (parent) => parent.created_at,
    updatedAt: (parent) => parent.updated_at,
  },
};

/**
 * FINAL EXPORT:
 *
 * Strongly-typed resolver combining queries, mutations, and field resolvers.
 */
export const dataModelResolvers: DataModelRelatedResolvers = {
  Query: queries,
  Mutation: mutations,
  ...dataModelTypeResolvers,
};
