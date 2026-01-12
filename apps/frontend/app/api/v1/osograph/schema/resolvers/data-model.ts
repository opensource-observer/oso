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
import { getResourceById } from "@/app/api/v1/osograph/utils/resolver-helpers";
import { FilterableConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import { createHash } from "crypto";
import {
  CreateDataModelReleaseSchema,
  CreateDataModelRevisionSchema,
  CreateDataModelSchema,
  UpdateDataModelSchema,
  DataModelReleaseWhereSchema,
  DataModelRevisionWhereSchema,
  DataModelWhereSchema,
  validateInput,
  MaterializationWhereSchema,
  RunWhereSchema,
} from "@/app/api/v1/osograph/utils/validation";
import { z } from "zod";
import { queryWithPagination } from "@/app/api/v1/osograph/utils/query-helpers";
import { ModelRow, ModelUpdate } from "@/lib/types/schema-types";

export const dataModelResolvers = {
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
    createDataModel: async (
      _: unknown,
      {
        input,
      }: {
        input: z.infer<typeof CreateDataModelSchema>;
      },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const validatedInput = validateInput(CreateDataModelSchema, input);
      await requireOrgMembership(
        authenticatedUser.userId,
        validatedInput.orgId,
      );

      const supabase = createAdminClient();
      const { data, error } = await supabase
        .from("model")
        .insert({
          org_id: validatedInput.orgId,
          dataset_id: validatedInput.datasetId,
          name: validatedInput.name,
          is_enabled: validatedInput.isEnabled,
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
    },
    updateDataModel: async (
      _: unknown,
      {
        input,
      }: {
        input: z.infer<typeof UpdateDataModelSchema>;
      },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const validatedInput = validateInput(UpdateDataModelSchema, input);
      const supabase = createAdminClient();

      const { data: dataModel, error: dataModelError } = await supabase
        .from("model")
        .select("org_id")
        .eq("id", validatedInput.dataModelId)
        .single();

      if (dataModelError || !dataModel) {
        throw ResourceErrors.notFound("DataModel", validatedInput.dataModelId);
      }

      await requireOrgMembership(authenticatedUser.userId, dataModel.org_id);

      const updateData: ModelUpdate = {};
      if (validatedInput.name !== undefined) {
        updateData.name = validatedInput.name;
      }
      if (validatedInput.isEnabled !== undefined) {
        updateData.is_enabled = validatedInput.isEnabled;
      }
      if (Object.keys(updateData).length > 0) {
        updateData.updated_at = new Date().toISOString();
      }

      const { data, error } = await supabase
        .from("model")
        .update(updateData)
        .eq("id", validatedInput.dataModelId)
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
    },
    createDataModelRevision: async (
      _: unknown,
      { input }: { input: z.infer<typeof CreateDataModelRevisionSchema> },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const validatedInput = validateInput(
        CreateDataModelRevisionSchema,
        input,
      );
      const supabase = createAdminClient();

      const { data: dataModel, error: dataModelError } = await supabase
        .from("model")
        .select("org_id")
        .eq("id", validatedInput.dataModelId)
        .single();

      if (dataModelError || !dataModel) {
        throw ResourceErrors.notFound("DataModel", validatedInput.dataModelId);
      }

      await requireOrgMembership(authenticatedUser.userId, dataModel.org_id);

      const { data: latestRevision } = await supabase
        .from("model_revision")
        .select("*")
        .eq("model_id", validatedInput.dataModelId)
        .order("revision_number", { ascending: false })
        .limit(1)
        .single();

      const hash = createHash("sha256")
        .update(
          JSON.stringify(
            Object.entries(validatedInput).sort((a, b) =>
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
          model_id: validatedInput.dataModelId,
          name: validatedInput.name,
          description: validatedInput.description,
          revision_number: revisionNumber,
          hash,
          language: validatedInput.language,
          code: validatedInput.code,
          cron: validatedInput.cron,
          start: validatedInput.start?.toISOString() ?? null,
          end: validatedInput.end?.toISOString() ?? null,
          schema: validatedInput.schema.map((col) => ({
            name: col.name,
            type: col.type,
            description: col.description ?? null,
          })),
          depends_on: validatedInput.dependsOn?.map((d) => ({
            model_id: d.dataModelId,
            alias: d.alias ?? null,
          })),
          partitioned_by: validatedInput.partitionedBy,
          clustered_by: validatedInput.clusteredBy,
          kind: validatedInput.kind,
          kind_options: validatedInput.kindOptions
            ? {
                time_column: validatedInput.kindOptions.timeColumn ?? null,
                time_column_format:
                  validatedInput.kindOptions.timeColumnFormat ?? null,
                batch_size: validatedInput.kindOptions.batchSize ?? null,
                lookback: validatedInput.kindOptions.lookback ?? null,
                unique_key_columns:
                  validatedInput.kindOptions.uniqueKeyColumns ?? null,
                when_matched_sql:
                  validatedInput.kindOptions.whenMatchedSql ?? null,
                merge_filter: validatedInput.kindOptions.mergeFilter ?? null,
                valid_from_name:
                  validatedInput.kindOptions.validFromName ?? null,
                valid_to_name: validatedInput.kindOptions.validToName ?? null,
                invalidate_hard_deletes:
                  validatedInput.kindOptions.invalidateHardDeletes ?? null,
                updated_at_column:
                  validatedInput.kindOptions.updatedAtColumn ?? null,
                updated_at_as_valid_from:
                  validatedInput.kindOptions.updatedAtAsValidFrom ?? null,
                scd_columns: validatedInput.kindOptions.scdColumns ?? null,
                execution_time_as_valid_from:
                  validatedInput.kindOptions.executionTimeAsValidFrom ?? null,
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
    },
    createDataModelRelease: async (
      _: unknown,
      { input }: { input: z.infer<typeof CreateDataModelReleaseSchema> },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const validatedInput = validateInput(CreateDataModelReleaseSchema, input);
      const supabase = createAdminClient();

      const { data: dataModel, error: dataModelError } = await supabase
        .from("model")
        .select("org_id")
        .eq("id", validatedInput.dataModelId)
        .single();

      if (dataModelError || !dataModel) {
        throw ResourceErrors.notFound("DataModel", validatedInput.dataModelId);
      }

      await requireOrgMembership(authenticatedUser.userId, dataModel.org_id);

      const { error: revisionError } = await supabase
        .from("model_revision")
        .select("id")
        .eq("id", validatedInput.dataModelRevisionId)
        .eq("model_id", validatedInput.dataModelId)
        .single();

      if (revisionError) {
        throw ResourceErrors.notFound(
          "DataModelRevision",
          validatedInput.dataModelRevisionId,
        );
      }

      const { data, error } = await supabase
        .from("model_release")
        .upsert({
          org_id: dataModel.org_id,
          model_id: validatedInput.dataModelId,
          model_revision_id: validatedInput.dataModelRevisionId,
          description: validatedInput.description,
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
    },
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

    materializations: async (
      parent: ModelRow,
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      return queryWithPagination(args, context, {
        tableName: "materialization",
        whereSchema: MaterializationWhereSchema,
        requireAuth: false,
        filterByUserOrgs: false,
        parentOrgIds: parent.org_id,
        basePredicate: {
          eq: [
            { key: "table_id", value: `data_model_${parent.id}` },
            { key: "dataset_id", value: parent.dataset_id },
          ],
        },
        orderBy: {
          key: "created_at",
          ascending: false,
        },
      });
    },
    runs: async (
      parent: ModelRow,
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
          eq: [{ key: "dataset_id", value: parent.dataset_id }],
          contains: [{ key: "models", value: [parent.id] }],
        },
        orderBy: {
          key: "queued_at",
          ascending: false,
        },
      });
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
