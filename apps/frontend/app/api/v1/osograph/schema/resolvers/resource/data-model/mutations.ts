import { logger } from "@/lib/logger";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import {
  ResourceErrors,
  ServerErrors,
} from "@/app/api/v1/osograph/utils/errors";
import {
  CreateDataModelReleaseSchema,
  CreateDataModelRevisionSchema,
  UpdateDataModelSchema,
  validateInput,
} from "@/app/api/v1/osograph/utils/validation";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import { ModelUpdate } from "@/lib/types/schema-types";
import { createHash } from "crypto";
import { getOrgResourceClient } from "@/app/api/v1/osograph/utils/access-control";
import {
  MutationCreateDataModelReleaseArgs,
  MutationCreateDataModelRevisionArgs,
  MutationDeleteDataModelArgs,
  MutationUpdateDataModelArgs,
} from "@/lib/graphql/generated/graphql";

/**
 * Data model mutations that operate on existing data model resources.
 * These resolvers use getOrgResourceClient for fine-grained permission checks.
 */
export const dataModelMutations: GraphQLResolverModule<GraphQLContext>["Mutation"] =
  {
    updateDataModel: async (
      _: unknown,
      { input }: MutationUpdateDataModelArgs,
      context: GraphQLContext,
    ) => {
      const validatedInput = validateInput(UpdateDataModelSchema, input);

      const { client } = await getOrgResourceClient(
        context,
        "data_model",
        validatedInput.dataModelId,
        "write",
      );

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

      const { data, error } = await client
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
      { input }: MutationCreateDataModelRevisionArgs,
      context: GraphQLContext,
    ) => {
      const validatedInput = validateInput(
        CreateDataModelRevisionSchema,
        input,
      );

      const { client } = await getOrgResourceClient(
        context,
        "data_model",
        validatedInput.dataModelId,
        "write",
      );

      const { data: dataModel, error: dataModelError } = await client
        .from("model")
        .select("org_id")
        .eq("id", validatedInput.dataModelId)
        .single();

      if (dataModelError || !dataModel) {
        throw ResourceErrors.notFound("DataModel", validatedInput.dataModelId);
      }

      const { data: latestRevision } = await client
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

      const { data, error } = await client
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
      { input }: MutationCreateDataModelReleaseArgs,
      context: GraphQLContext,
    ) => {
      const validatedInput = validateInput(CreateDataModelReleaseSchema, input);

      const { client } = await getOrgResourceClient(
        context,
        "data_model",
        validatedInput.dataModelId,
        "write",
      );

      const { data: dataModel, error: dataModelError } = await client
        .from("model")
        .select("org_id")
        .eq("id", validatedInput.dataModelId)
        .single();

      if (dataModelError || !dataModel) {
        throw ResourceErrors.notFound("DataModel", validatedInput.dataModelId);
      }

      const { error: revisionError } = await client
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

      const { data, error } = await client
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

    deleteDataModel: async (
      _: unknown,
      { id }: MutationDeleteDataModelArgs,
      context: GraphQLContext,
    ) => {
      const { client } = await getOrgResourceClient(
        context,
        "data_model",
        id,
        "admin",
      );

      const { error } = await client
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
  };
