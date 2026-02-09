import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import {
  ServerErrors,
  ValidationErrors,
} from "@/app/api/v1/osograph/utils/errors";
import {
  validateInput,
  UpdateModelContextSchema,
} from "@/app/api/v1/osograph/utils/validation";
import { logger } from "@/lib/logger";
import { generateTableId } from "@/app/api/v1/osograph/utils/model";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import { getOrgResourceClient } from "@/app/api/v1/osograph/utils/access-control";
import { MutationUpdateModelContextArgs } from "@/lib/graphql/generated/graphql";

/**
 * Model context mutations that operate on existing dataset resources.
 * Uses getOrgResourceClient with dataset as the resource type since
 * model context is scoped to a dataset.
 */
export const modelContextMutations: GraphQLResolverModule<GraphQLContext>["Mutation"] =
  {
    updateModelContext: async (
      _: unknown,
      { input }: MutationUpdateModelContextArgs,
      context: GraphQLContext,
    ) => {
      const validatedInput = validateInput(UpdateModelContextSchema, input);
      const {
        datasetId,
        modelId,
        context: modelContext,
        columnContext,
      } = validatedInput;

      const { client } = await getOrgResourceClient(
        context,
        "dataset",
        datasetId,
        "write",
      );

      // Check access to dataset
      const { data: dataset, error: datasetError } = await client
        .from("datasets")
        .select("org_id, dataset_type")
        .eq("id", datasetId)
        .single();

      if (datasetError || !dataset) {
        throw ValidationErrors.invalidInput("datasetId", "Dataset not found");
      }

      const tableId = generateTableId(dataset.dataset_type, modelId);

      // Check if context exists
      const { data: existingContext } = await client
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
        const result = await client
          .from("model_contexts")
          .update(payload)
          .eq("id", existingContext.id)
          .select()
          .single();
        upsertedData = result.data;
        upsertError = result.error;
      } else {
        const result = await client
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
  };
