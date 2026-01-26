import { createAdminClient } from "@/lib/supabase/admin";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import {
  ServerErrors,
  ValidationErrors,
} from "@/app/api/v1/osograph/utils/errors";
import {
  validateInput,
  UpdateModelContextSchema,
} from "@/app/api/v1/osograph/utils/validation";
import { z } from "zod";
import {
  requireOrgMembership,
  requireAuthentication,
} from "@/app/api/v1/osograph/utils/auth";
import { logger } from "@/lib/logger";
import { generateTableId } from "@/app/api/v1/osograph/utils/model";
import { ModelContextsRow } from "@/lib/types/schema-types";

export async function getModelContext(datasetId: string, tableId: string) {
  const supabase = createAdminClient();
  const { data, error } = await supabase
    .from("model_contexts")
    .select("*")
    .eq("dataset_id", datasetId)
    .eq("table_id", tableId)
    .is("deleted_at", null)
    .maybeSingle();

  if (error) {
    logger.error(
      `Error fetching model context for ${datasetId}/${tableId}: ${error.message}`,
    );
    throw ServerErrors.database("Failed to fetch model context");
  }

  if (!data) return null;

  return data;
}

export const modelContextResolvers = {
  Mutation: {
    updateModelContext: async (
      _: unknown,
      { input }: { input: z.infer<typeof UpdateModelContextSchema> },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const validatedInput = validateInput(UpdateModelContextSchema, input);
      const {
        datasetId,
        modelId,
        context: modelContext,
        columnContext,
      } = validatedInput;

      const supabase = createAdminClient();
      // Check access to dataset
      const { data: dataset, error: datasetError } = await supabase
        .from("datasets")
        .select("org_id, dataset_type")
        .eq("id", datasetId)
        .single();

      if (datasetError || !dataset) {
        throw ValidationErrors.invalidInput("datasetId", "Dataset not found");
      }

      await requireOrgMembership(authenticatedUser.userId, dataset.org_id);

      const tableId = generateTableId(dataset.dataset_type, modelId);

      // Check if context exists
      const { data: existingContext } = await supabase
        .from("model_contexts")
        .select("id")
        .eq("dataset_id", datasetId)
        .eq("table_id", tableId)
        .is("deleted_at", null)
        .maybeSingle();

      let upsertedData;
      let upsertError;

      const payload = {
        org_id: dataset.org_id,
        dataset_id: datasetId,
        table_id: tableId,
        context: modelContext,
        column_context: columnContext,
        updated_at: new Date().toISOString(),
      };

      if (existingContext) {
        const result = await supabase
          .from("model_contexts")
          .update(payload)
          .eq("id", existingContext.id)
          .select()
          .single();
        upsertedData = result.data;
        upsertError = result.error;
      } else {
        const result = await supabase
          .from("model_contexts")
          .insert(payload)
          .select()
          .single();
        upsertedData = result.data;
        upsertError = result.error;
      }

      if (upsertError || !upsertedData) {
        logger.error(`Failed to update model context: ${upsertError?.message}`);
        throw ServerErrors.database("Failed to update model context");
      }

      return {
        success: true,
        message: "Model context updated successfully",
        modelContext: upsertedData,
      };
    },
  },
  ModelContext: {
    orgId: (parent: ModelContextsRow) => parent.org_id,
    datasetId: (parent: ModelContextsRow) => parent.dataset_id,
    tableId: (parent: ModelContextsRow) => parent.table_id,
    context: (parent: ModelContextsRow) => parent.context,
    columnContext: (parent: ModelContextsRow) => parent.column_context,
    createdAt: (parent: ModelContextsRow) => parent.created_at,
    updatedAt: (parent: ModelContextsRow) => parent.updated_at,
  },
};
