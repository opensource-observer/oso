import { getSystemClient } from "@/app/api/v1/osograph/utils/access-control";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import {
  ResourceErrors,
  ServerErrors,
  ValidationErrors,
} from "@/app/api/v1/osograph/utils/errors";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import {
  CreateMaterializationSchema,
  validateInput,
} from "@/app/api/v1/osograph/utils/validation";
import { logger } from "@/lib/logger";
import { validateTableId } from "@/app/api/v1/osograph/utils/model";
import { MutationCreateMaterializationArgs } from "@/lib/graphql/generated/graphql";

export const materializationMutationResolvers: GraphQLResolverModule<GraphQLContext> =
  {
    Mutation: {
      createMaterialization: async (
        _: unknown,
        args: MutationCreateMaterializationArgs,
        context: GraphQLContext,
      ) => {
        const client = getSystemClient(context);

        const { stepId, tableId, schema, warehouseFqn } = validateInput(
          CreateMaterializationSchema,
          args.input,
        );

        // Assert that the tableId has one of the appropriate prefixes
        validateTableId(tableId);

        logger.info(`Creating materialization for step ${stepId}`);

        // Get the step
        const { data: stepData, error: stepError } = await client
          .from("step")
          .select("*")
          .eq("id", stepId)
          .single();
        if (stepError || !stepData) {
          logger.error(`Step ${stepId} not found: ${stepError?.message}`);
          throw ResourceErrors.notFound(`Step ${stepId} not found`);
        }

        // Get the dataset id from the run associated with the step
        const { data: runData, error: runError } = await client
          .from("run")
          .select("id, org_id, dataset_id")
          .eq("id", stepData.run_id)
          .single();
        if (runError || !runData) {
          logger.error(
            `Run for step ${stepId} not found: ${runError?.message}`,
          );
          throw ResourceErrors.notFound(`Run for step ${stepId} not found`);
        }

        if (runData.dataset_id === null) {
          logger.error(`Dataset ID for run ${runData.id} is null`);
          throw ValidationErrors.invalidInput(
            "stepId",
            `Associated run ${runData.id} does not have a dataset_id. ` +
              "Can only create materializations for dataset runs.",
          );
        }

        // Convert schema object to supported format (remove undefined)
        const dbSafeSchema = schema.map((entry) => {
          return {
            name: entry.name,
            type: entry.type,
            description: entry.description || null,
          };
        });

        // Create the materialization
        const { data: materializationData, error: materializationError } =
          await client
            .from("materialization")
            .insert({
              run_id: runData.id,
              org_id: runData.org_id,
              dataset_id: runData.dataset_id,
              step_id: stepId,
              schema: dbSafeSchema,
              created_at: new Date().toISOString(),
              table_id: tableId,
              warehouse_fqn: warehouseFqn,
            })
            .select()
            .single();
        if (materializationError || !materializationData) {
          throw ServerErrors.internal(
            `Failed to create materialization for step ${stepId}`,
          );
        }

        return {
          message: "Created materialization",
          success: true,
          materialization: materializationData,
        };
      },
    },
  };
