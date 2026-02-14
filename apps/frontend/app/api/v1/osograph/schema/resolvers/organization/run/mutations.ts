import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import { getOrgScopedClient } from "@/app/api/v1/osograph/utils/access-control";
import { getDatasetById } from "@/app/api/v1/osograph/utils/resolver-helpers";
import { createQueueService } from "@/lib/services/queue";
import {
  ResourceErrors,
  ServerErrors,
} from "@/app/api/v1/osograph/utils/errors";
import {
  CreateDataIngestionRunRequestSchema,
  CreateStaticModelRunRequestSchema,
  CreateUserModelRunRequestSchema,
  validateInput,
} from "@/app/api/v1/osograph/utils/validation";
import { DataModelRunRequest } from "@opensource-observer/osoprotobufs/data-model";
import { DataIngestionRunRequest } from "@opensource-observer/osoprotobufs/data-ingestion";
import { StaticModelRunRequest } from "@opensource-observer/osoprotobufs/static-model";
import type {
  MutationCreateDataIngestionRunRequestArgs,
  MutationCreateStaticModelRunRequestArgs,
  MutationCreateUserModelRunRequestArgs,
} from "@/lib/graphql/generated/graphql";
import type { SupabaseAdminClient } from "@/lib/supabase/admin";
import type { DatasetsRow, RunRow } from "@/lib/types/schema-types";
import type {
  ProtobufEncoder,
  ProtobufMessage,
} from "@/lib/services/queue/types";
import { logger } from "@/lib/logger";

async function createRunRequest<
  TInput extends { datasetId: string; selectedModels?: string[] },
  TMessage extends ProtobufMessage,
>(
  context: GraphQLContext,
  input: TInput,
  queueName: string,
  encoder: ProtobufEncoder<TMessage>,
  messageFactory: (
    dataset: DatasetsRow,
    run: RunRow,
    client: SupabaseAdminClient,
  ) => Promise<TMessage>,
) {
  const dataset = await getDatasetById(input.datasetId);
  const { client, userId } = await getOrgScopedClient(context, dataset.org_id);

  const { data: run, error: runError } = await client
    .from("run")
    .insert({
      org_id: dataset.org_id,
      dataset_id: input.datasetId,
      run_type: "manual",
      requested_by: userId,
      models: input.selectedModels || [],
    })
    .select()
    .single();

  if (runError || !run) {
    logger.error(
      `Error creating run for dataset ${input.datasetId}: ${runError?.message}`,
    );
    throw ServerErrors.database("Failed to create run request");
  }

  const message = await messageFactory(dataset, run, client);
  const queueService = createQueueService();
  const result = await queueService.queueMessage({
    queueName,
    message,
    encoder,
  });

  if (!result.success) {
    logger.error(
      `Failed to publish message to queue: ${result.error?.message}`,
    );
    throw ServerErrors.queueError(
      result.error?.message || "Failed to publish to queue",
    );
  }

  logger.info(
    `Published ${queueName} message to queue. MessageId: ${result.messageId}`,
  );

  return {
    success: true,
    message: "Run request created successfully",
    run,
  };
}

export const runMutations: GraphQLResolverModule<GraphQLContext>["Mutation"] = {
  createUserModelRunRequest: async (
    _: unknown,
    args: MutationCreateUserModelRunRequestArgs,
    context: GraphQLContext,
  ) => {
    const input = validateInput(CreateUserModelRunRequestSchema, args.input);

    return createRunRequest(
      context,
      input,
      "data_model_run_requests",
      DataModelRunRequest,
      async (_dataset, run) => {
        const runIdBuffer = Buffer.from(run.id.replace(/-/g, ""), "hex");
        return {
          runId: new Uint8Array(runIdBuffer),
          datasetId: _dataset.id,
          modelReleaseIds: input.selectedModels || [],
        };
      },
    );
  },

  createDataIngestionRunRequest: async (
    _: unknown,
    args: MutationCreateDataIngestionRunRequestArgs,
    context: GraphQLContext,
  ) => {
    const input = validateInput(
      CreateDataIngestionRunRequestSchema,
      args.input,
    );

    return createRunRequest(
      context,
      input,
      "data_ingestion_run_requests",
      DataIngestionRunRequest,
      async (_dataset, run, client) => {
        const { data: config, error: configError } = await client
          .from("data_ingestions")
          .select("*")
          .eq("dataset_id", input.datasetId)
          .is("deleted_at", null)
          .single();

        if (configError || !config) {
          logger.error(
            `Error fetching config for dataset ${input.datasetId}: ${configError?.message}`,
          );
          throw ResourceErrors.notFound("Config not found for dataset");
        }

        const runIdBuffer = Buffer.from(run.id.replace(/-/g, ""), "hex");
        return {
          runId: new Uint8Array(runIdBuffer),
          datasetId: _dataset.id,
        };
      },
    );
  },

  createStaticModelRunRequest: async (
    _: unknown,
    args: MutationCreateStaticModelRunRequestArgs,
    context: GraphQLContext,
  ) => {
    const input = validateInput(CreateStaticModelRunRequestSchema, args.input);

    return createRunRequest(
      context,
      input,
      "static_model_run_requests",
      StaticModelRunRequest,
      async (_dataset, run) => {
        const runIdBuffer = Buffer.from(run.id.replace(/-/g, ""), "hex");
        return {
          runId: new Uint8Array(runIdBuffer),
          datasetId: _dataset.id,
          modelIds: input.selectedModels || [],
        };
      },
    );
  },
};
