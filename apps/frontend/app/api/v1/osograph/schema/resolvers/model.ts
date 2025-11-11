import { createAdminClient } from "@/lib/supabase/admin";
import { logger } from "@/lib/logger";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import {
  requireAuthentication,
  requireOrgMembership,
  getOrganization,
  getUserOrgIds,
} from "@/app/api/v1/osograph/utils/auth";
import {
  ResourceErrors,
  ServerErrors,
} from "@/app/api/v1/osograph/utils/errors";
import {
  buildConnectionOrEmpty,
  getResourceById,
  preparePaginationRange,
} from "@/app/api/v1/osograph/utils/resolver-helpers";
import { ConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import { createHash } from "crypto";
import {
  validateInput,
  CreateModelSchema,
  CreateModelRevisionSchema,
  CreateModelReleaseSchema,
} from "@/app/api/v1/osograph/utils/validation";
import { z } from "zod";

export async function getModelsConnection(
  orgIds: string[],
  args: ConnectionArgs & {
    datasetId?: string;
  },
) {
  const supabase = createAdminClient();
  let query = supabase
    .from("model")
    .select("*", { count: "exact" })
    .in("org_id", orgIds)
    .is("deleted_at", null);

  if (args.datasetId) {
    query = query.eq("dataset_id", args.datasetId);
  }

  const [start, end] = preparePaginationRange(args);
  query = query.range(start, end);

  const { data: models, error, count } = await query;

  if (error) {
    logger.error("Failed to fetch models:", error);
    throw ServerErrors.database("Failed to fetch models");
  }

  return buildConnectionOrEmpty(models, args, count);
}

export const modelResolvers = {
  Query: {
    model: async (
      _: unknown,
      args: { id: string },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const supabase = createAdminClient();

      const { data: model, error } = await supabase
        .from("model")
        .select("*")
        .eq("id", args.id)
        .is("deleted_at", null)
        .single();

      if (error || !model) {
        return null;
      }
      await requireOrgMembership(authenticatedUser.userId, model.org_id);

      return model;
    },
    models: async (
      _: unknown,
      args: ConnectionArgs,
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const orgIds = await getUserOrgIds(authenticatedUser.userId);
      if (orgIds.length === 0) {
        return buildConnectionOrEmpty(null, args, 0);
      }
      return getModelsConnection(orgIds, args);
    },
  },
  Mutation: {
    createModel: async (
      _: unknown,
      {
        input,
      }: {
        input: z.infer<typeof CreateModelSchema>;
      },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const validatedInput = validateInput(CreateModelSchema, input);
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
        logger.error("Failed to create model:", error);
        throw ServerErrors.database("Failed to create model");
      }

      return {
        success: true,
        message: "Model created successfully",
        model: data,
      };
    },
    createModelRevision: async (
      _: unknown,
      { input }: { input: z.infer<typeof CreateModelRevisionSchema> },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const validatedInput = validateInput(CreateModelRevisionSchema, input);
      const supabase = createAdminClient();

      const { data: model, error: modelError } = await supabase
        .from("model")
        .select("org_id")
        .eq("id", validatedInput.modelId)
        .single();

      if (modelError || !model) {
        throw ResourceErrors.notFound("Model", validatedInput.modelId);
      }

      await requireOrgMembership(authenticatedUser.userId, model.org_id);

      const { data: latestRevision } = await supabase
        .from("model_revision")
        .select("revision_number, hash")
        .eq("model_id", validatedInput.modelId)
        .order("revision_number", { ascending: false })
        .limit(1)
        .single();

      const {
        name: _name,
        displayName: _displayName,
        description: _description,
        ...config
      } = validatedInput;
      const hash = createHash("sha256")
        .update(
          JSON.stringify(
            Object.entries(config).sort((a, b) => a[0].localeCompare(b[0])),
          ),
        )
        .digest("hex");

      if (latestRevision?.hash === hash) {
        return {
          success: true,
          message: "No changes detected, returning existing revision",
          modelRevision: latestRevision,
        };
      }

      const revisionNumber = (latestRevision?.revision_number || 0) + 1;

      const { data, error } = await supabase
        .from("model_revision")
        .insert({
          org_id: model.org_id,
          model_id: validatedInput.modelId,
          name: validatedInput.name,
          display_name: validatedInput.displayName,
          description: validatedInput.description,
          revision_number: revisionNumber,
          hash,
          language: validatedInput.language,
          code: validatedInput.code,
          cron: validatedInput.cron,
          start: validatedInput.start,
          end: validatedInput.end,
          schema: validatedInput.schema.map((col) => ({
            name: col.name,
            type: col.type,
            description: col.description ?? null,
          })),
          depends_on: validatedInput.dependsOn?.map((d) => ({
            model_id: d.modelId,
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
        logger.error("Failed to create model revision:", error);
        throw ServerErrors.database("Failed to create model revision");
      }

      return {
        success: true,
        message: "Model revision created successfully",
        modelRevision: data,
      };
    },
    createModelRelease: async (
      _: unknown,
      { input }: { input: z.infer<typeof CreateModelReleaseSchema> },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const validatedInput = validateInput(CreateModelReleaseSchema, input);
      const supabase = createAdminClient();

      const { data: model, error: modelError } = await supabase
        .from("model")
        .select("org_id")
        .eq("id", validatedInput.modelId)
        .single();

      if (modelError || !model) {
        throw ResourceErrors.notFound("Model", validatedInput.modelId);
      }

      await requireOrgMembership(authenticatedUser.userId, model.org_id);

      const { error: revisionError } = await supabase
        .from("model_revision")
        .select("id")
        .eq("id", validatedInput.modelRevisionId)
        .eq("model_id", validatedInput.modelId)
        .single();

      if (revisionError) {
        throw ResourceErrors.notFound(
          "ModelRevision",
          validatedInput.modelRevisionId,
        );
      }

      const { data, error } = await supabase
        .from("model_release")
        .insert({
          org_id: model.org_id,
          model_id: validatedInput.modelId,
          model_revision_id: validatedInput.modelRevisionId,
          description: validatedInput.description,
        })
        .select()
        .single();

      if (error) {
        logger.error("Failed to create model release:", error);
        throw ServerErrors.database("Failed to create model release");
      }

      return {
        success: true,
        message: "Model release created successfully",
        modelRelease: data,
      };
    },
  },
  Model: {
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
    revisions: async (parent: { id: string }, args: ConnectionArgs) => {
      const supabase = createAdminClient();
      const [start, end] = preparePaginationRange(args);
      const { data, error, count } = await supabase
        .from("model_revision")
        .select("*", { count: "exact" })
        .eq("model_id", parent.id)
        .order("revision_number", { ascending: false })
        .range(start, end);

      if (error) {
        logger.error(
          `Failed to fetch revisions for model ${parent.id}:`,
          error,
        );
        return buildConnectionOrEmpty(null, args, 0);
      }
      return buildConnectionOrEmpty(data, args, count);
    },
    releases: async (parent: { id: string }, args: ConnectionArgs) => {
      const supabase = createAdminClient();
      const [start, end] = preparePaginationRange(args);
      const { data, error, count } = await supabase
        .from("model_release")
        .select("*", { count: "exact" })
        .eq("model_id", parent.id)
        .order("created_at", { ascending: false })
        .range(start, end);

      if (error) {
        logger.error(`Failed to fetch releases for model ${parent.id}:`, error);
        return buildConnectionOrEmpty(null, args, 0);
      }
      return buildConnectionOrEmpty(data, args, count);
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
  },

  ModelRevision: {
    orgId: (parent: { org_id: string }) => parent.org_id,
    modelId: (parent: { model_id: string }) => parent.model_id,
    model: async (parent: { model_id: string }) => {
      const supabase = createAdminClient();
      const { data, error } = await supabase
        .from("model")
        .select("*")
        .eq("id", parent.model_id)
        .single();
      if (error) {
        throw ResourceErrors.notFound("Model", parent.model_id);
      }
      return data;
    },
    organization: (parent: { org_id: string }) => {
      return getOrganization(parent.org_id);
    },
    displayName: (parent: { display_name: string }) => parent.display_name,
    revisionNumber: (parent: { revision_number: number }) =>
      parent.revision_number,
    start: (parent: { start: string | null }) => parent.start,
    end: (parent: { end: string | null }) => parent.end,
    dependsOn: (parent: { depends_on: any[] }) => parent.depends_on,
    partitionedBy: (parent: { partitioned_by: string[] }) =>
      parent.partitioned_by,
    clusteredBy: (parent: { clustered_by: string[] }) => parent.clustered_by,
    kindOptions: (parent: { kind_options: any }) => parent.kind_options,
    createdAt: (parent: { created_at: string }) => parent.created_at,
  },

  ModelRelease: {
    orgId: (parent: { org_id: string }) => parent.org_id,
    modelId: (parent: { model_id: string }) => parent.model_id,
    revisionId: (parent: { model_revision_id: string }) =>
      parent.model_revision_id,
    model: async (parent: { model_id: string }) => {
      const supabase = createAdminClient();
      const { data, error } = await supabase
        .from("model")
        .select("*")
        .eq("id", parent.model_id)
        .single();
      if (error) {
        throw ResourceErrors.notFound("Model", parent.model_id);
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
          "ModelRevision",
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
