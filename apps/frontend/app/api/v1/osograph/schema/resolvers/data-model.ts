import { createAdminClient } from "@/lib/supabase/admin";
import { logger } from "@/lib/logger";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import {
  getOrganization,
  requireAuthentication,
  requireOrgMembership,
} from "@/app/api/v1/osograph/utils/auth";
import {
  ResourceErrors,
  ServerErrors,
} from "@/app/api/v1/osograph/utils/errors";
import {
  getMaterializations,
  getModelRunConnection,
  getResourceById,
} from "@/app/api/v1/osograph/utils/resolver-helpers";
import {
  ConnectionArgs,
  FilterableConnectionArgs,
} from "@/app/api/v1/osograph/utils/pagination";
import { createHash } from "crypto";
import {
  CreateDataModelReleaseSchema,
  DataModelReleaseWhereSchema,
  DataModelRevisionWhereSchema,
  DataModelWhereSchema,
  validateInput,
} from "@/app/api/v1/osograph/utils/validation";
import { z } from "zod";
import { queryWithPagination } from "@/app/api/v1/osograph/utils/query-helpers";
import { ModelRow, ModelUpdate } from "@/lib/types/schema-types";
import { getModelContext } from "@/app/api/v1/osograph/schema/resolvers/model-context";
import {
  executePreviewQuery,
  generateTableId,
} from "@/app/api/v1/osograph/utils/model";
import { PreviewData } from "@/lib/graphql/generated/graphql";
import { MutationResolvers, QueryResolvers, ResolversTypes } from "@/app/api/v1/osograph/types/generated/types";
import { createResolver, ResolverTypeKeys } from "../../utils/resolver-builder";
import { requireAuth, ensureOrgMembership, withValidation } from "../../utils/resolver-middleware";
import { CreateDataModelInputSchema, CreateDataModelReleaseInputSchema, CreateDataModelRevisionInputSchema, UpdateDataModelInputSchema } from "@/app/api/v1/osograph/types/generated/validation";

type DataModelQueryResolvers = Pick<QueryResolvers, "dataModels">;
type DataModelMutationResolvers = Pick<Required<MutationResolvers>, "createDataModel" | "updateDataModel" | "createDataModelRevision" | "createDataModelRelease" | "deleteDataModel">;
type DataModelResolverTypes = Pick<ResolversTypes, "DataModel" | "DataModelRevision" | "DataModelRelease">;

type DataModelResolvers = {
  Query: DataModelQueryResolvers;
  Mutation: DataModelMutationResolvers;
} & DataModelResolverTypes;

const queryResolvers: DataModelQueryResolvers = {
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
  }
}

function existingDataModelResolver<TResult extends ResolverTypeKeys, TSchema extends z.ZodSchema>(schema: TSchema, getExistingModelId: (input: z.infer<TSchema>) => string) {
  return createResolver<TResult>()
    .use(requireAuth())
    .use(withValidation(schema))
    .use(async (context, args) => {
      const existingModelId = getExistingModelId(args.input);
      const supabase = createAdminClient();
      const { data: dataModel, error: dataModelError } = await supabase
        .from("model")
        .select("org_id")
        .eq("id", existingModelId)
        .single();
      if (dataModelError || !dataModel) {
        throw ResourceErrors.notFound("DataModel", args.input.dataModelId);
      }
      return {
        context: {
          ...context,
          dataModel: dataModel,
          supabase: supabase,
        },
        args,
      }
    })
    .use(ensureOrgMembership(({ context }) => context.dataModel.org_id));
}

/**
 * NEW STYLE MUTATION RESOLVERS:
 * 
 * Strongly typed, with middleware for authentication, validation, and org membership.
 */
const mutations: DataModelMutationResolvers = {
  createDataModel: createResolver<"CreateDataModelPayload">()
    .use(requireAuth())
    .use(withValidation(CreateDataModelInputSchema()))
    .use(ensureOrgMembership(({ args }) => args.input.orgId))
    .resolve(async (_, { input }) => {
      const supabase = createAdminClient();
      const { data, error } = await supabase
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
    }),
  updateDataModel: existingDataModelResolver<"CreateDataModelPayload", ReturnType<typeof UpdateDataModelInputSchema>>(
    UpdateDataModelInputSchema(),
    (input) => input.dataModelId
  )
    .resolve(async (_, { input }, context) => {
      const { supabase } = context;
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

      const { data, error } = await supabase
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
    }),
  createDataModelRevision: existingDataModelResolver<"CreateDataModelRevisionPayload", ReturnType<typeof CreateDataModelRevisionInputSchema>>(
    CreateDataModelRevisionInputSchema(),
    (input) => input.dataModelId
  )
    .resolve(async (_, { input }, context) => {
      const { supabase, dataModel } = context;
      const { data: latestRevision } = await supabase
        .from("model_revision")
        .select("*")
        .eq("model_id", input.dataModelId)
        .order("revision_number", { ascending: false })
        .limit(1)
        .single();

      const hash = createHash("sha256")
        .update(
          JSON.stringify(
            Object.entries(input).sort((a, b) =>
              a[0].localeCompare(b[0]),
            ),
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

      const { data, error } = await supabase
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
          start: input.start?.toISOString() ?? null,
          end: input.end?.toISOString() ?? null,
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
              time_column_format:
                input.kindOptions.timeColumnFormat ?? null,
              batch_size: input.kindOptions.batchSize ?? null,
              lookback: input.kindOptions.lookback ?? null,
              unique_key_columns:
                input.kindOptions.uniqueKeyColumns ?? null,
              when_matched_sql:
                input.kindOptions.whenMatchedSql ?? null,
              merge_filter: input.kindOptions.mergeFilter ?? null,
              valid_from_name:
                input.kindOptions.validFromName ?? null,
              valid_to_name: input.kindOptions.validToName ?? null,
              invalidate_hard_deletes:
                input.kindOptions.invalidateHardDeletes ?? null,
              updated_at_column:
                input.kindOptions.updatedAtColumn ?? null,
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
    }),
  createDataModelRelease: existingDataModelResolver<"CreateDataModelReleasePayload", ReturnType<typeof CreateDataModelReleaseInputSchema>>(
    CreateDataModelReleaseInputSchema(),
    (input) => input.dataModelId
  )
    .resolve(async (_, { input }, context) => {
      const { supabase, dataModel } = context;
      const { error: revisionError } = await supabase
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

      const { data, error } = await supabase
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
    }),
}

// OLD STYLE
const mutationResolvers: DataModelMutationResolvers = {
  deleteDataModel: async (
    _: unknown,
    { id }: { id: string },
    context: GraphQLContext,
  ) => {
    const authenticatedUser = requireAuthentication(context.user);
    const supabase = createAdminClient();

    const { data: dataModel, error: fetchError } = await supabase
      .from("model")
      .select("org_id")
      .eq("id", id)
      .single();

    if (fetchError || !dataModel) {
      throw ResourceErrors.notFound("DataModel", id);
    }

    await requireOrgMembership(authenticatedUser.userId, dataModel.org_id);

    const { error } = await supabase
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
  },
}


export const dataModelResolvers: DataModelResolvers = {
  Query: {
    dataModels: async (
      _: unknown,
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
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
  },
  Mutation: {

  },
  DataModel: {
    orgId: (parent: { org_id: string }) => parent.org_id,
    organization: (parent: { org_id: string }) => {
      return getOrganization(parent.org_id);
    },
    dataset: (parent: { dataset_id: string }) => {
      return getResourceById({
        tableName: "datasets",
        id: parent.dataset_id,
        userId: "",
      });
    },
    revisions: async (
      parent: { id: string; org_id: string },
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
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
    releases: async (
      parent: { id: string; org_id: string },
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
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
    isEnabled: (parent: { is_enabled: boolean }) => parent.is_enabled,
    createdAt: (parent: { created_at: string }) => parent.created_at,
    updatedAt: (parent: { updated_at: string }) => parent.updated_at,
    latestRevision: async (parent: { id: string }) => {
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
    latestRelease: async (parent: { id: string }) => {
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

    runs: async (parent: ModelRow, args: ConnectionArgs) => {
      return getModelRunConnection(parent.dataset_id, parent.id, args);
    },
    modelContext: async (parent: ModelRow) => {
      return getModelContext(parent.dataset_id, parent.id);
    },
    materializations: async (
      parent: ModelRow,
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      return getMaterializations(
        args,
        context,
        parent.org_id,
        parent.dataset_id,
        generateTableId("USER_MODEL", parent.id),
      );
    },
    previewData: async (
      parent: ModelRow,
      _args: Record<string, never>,
      context: GraphQLContext,
    ): Promise<PreviewData> => {
      const authenticatedUser = requireAuthentication(context.user);

      const tableId = generateTableId("USER_MODEL", parent.id);

      return executePreviewQuery(
        parent.org_id,
        parent.dataset_id,
        tableId,
        authenticatedUser,
        parent.name,
      );
    },
  },

  DataModelRevision: {
    orgId: (parent: { org_id: string }) => parent.org_id,
    dataModelId: (parent: { model_id: string }) => parent.model_id,
    dataModel: async (parent: { model_id: string }) => {
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
    organization: (parent: { org_id: string }) => {
      return getOrganization(parent.org_id);
    },
    revisionNumber: (parent: { revision_number: number }) =>
      parent.revision_number,
    start: (parent: { start: string | null }) => parent.start,
    end: (parent: { end: string | null }) => parent.end,
    dependsOn: (parent: { depends_on: unknown[] }) => parent.depends_on,
    partitionedBy: (parent: { partitioned_by: string[] }) =>
      parent.partitioned_by,
    clusteredBy: (parent: { clustered_by: string[] }) => parent.clustered_by,
    kindOptions: (parent: { kind_options: unknown }) => parent.kind_options,
    createdAt: (parent: { created_at: string }) => parent.created_at,
  },

  DataModelRelease: {
    orgId: (parent: { org_id: string }) => parent.org_id,
    dataModelId: (parent: { model_id: string }) => parent.model_id,
    revisionId: (parent: { model_revision_id: string }) =>
      parent.model_revision_id,
    dataModel: async (parent: { model_id: string }) => {
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
    revision: async (parent: { model_revision_id: string }) => {
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
    organization: (parent: { org_id: string }) => {
      return getOrganization(parent.org_id);
    },
    createdAt: (parent: { created_at: string }) => parent.created_at,
    updatedAt: (parent: { updated_at: string }) => parent.updated_at,
  },
};
