import {
  DatasetsRow,
  MaterializationRow,
  RunRow,
} from "@/lib/types/schema-types";
import {
  RunStatus,
  RunTriggerType,
  RunType,
} from "@/lib/graphql/generated/graphql";
import { queryWithPagination } from "@/app/api/v1/osograph/utils/query-helpers";
import { FilterableConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import {
  CreateUserModelRunRequestSchema,
  MaterializationWhereSchema,
  validateInput,
} from "@/app/api/v1/osograph/utils/validation";
import { assertNever } from "@opensource-observer/utils";
import { logger } from "@/lib/logger";
import { createAdminClient } from "@/lib/supabase/admin";
import {
  AuthenticationErrors,
  ResourceErrors,
  ServerErrors,
} from "@/app/api/v1/osograph/utils/errors";
import z from "zod";
import { requireAuthentication } from "@/app/api/v1/osograph/utils/auth";
import { checkMembershipExists } from "@/app/api/v1/osograph/utils/resolver-helpers";
import { createQueueService } from "@/lib/services/queue";
import { DataModelRunRequest } from "@/lib/proto/generated/data-model";

function mapRunStatus(status: RunRow["status"]): RunStatus {
  switch (status) {
    case "running":
      return RunStatus.Running;
    case "completed":
      return RunStatus.Success;
    case "failed":
      return RunStatus.Failed;
    case "canceled":
      return RunStatus.Canceled;
    case "queued":
      return RunStatus.Queued;
    default:
      assertNever(status, `Unknown run status: ${status}`);
  }
}

function genericRunRequestResolver<T extends z.ZodTypeAny>(
  inputSchema: T,
  queueMessageFactory: (
    input: z.infer<T>,
    user: ReturnType<typeof requireAuthentication>,
    dataset: DatasetsRow,
    run: RunRow,
  ) => Promise<DataModelRunRequest>,
): (
  _: any,
  args: { input: z.infer<T> },
  context: GraphQLContext,
) => Promise<{
  success: boolean;
  message: string;
  run: RunRow;
}> {
  return async (
    _: any,
    args: { input: z.infer<T> },
    context: GraphQLContext,
  ) => {
    const authenticatedUser = requireAuthentication(context.user);
    const input = validateInput(inputSchema, args.input);
    const supabase = createAdminClient();

    // We need to get the org from the dataset and then verify the user belongs to that org
    // First, get the dataset
    const { datasetId } = input;
    const { data: dataset, error: datasetError } = await supabase
      .from("datasets")
      .select("*")
      .eq("id", datasetId)
      .single();
    if (datasetError || !dataset) {
      logger.error(
        `Error fetching dataset with id ${datasetId}: ${datasetError?.message}`,
      );
      throw ResourceErrors.notFound("Dataset not found");
    }

    // Now verify the user belongs to that org
    if (
      !(await checkMembershipExists(authenticatedUser.userId, dataset.org_id))
    ) {
      throw AuthenticationErrors.notAuthorized();
    }

    // Create a run to store the results of the run request
    const { data: queuedRun, error: queuedRunError } = await supabase
      .from("run")
      .insert({
        org_id: dataset.org_id,
        dataset_id: datasetId,
        run_type: "manual",
        requested_by: authenticatedUser.userId,
      })
      .select()
      .single();
    if (queuedRunError || !queuedRun) {
      logger.error(
        `Error creating run for dataset ${datasetId}: ${queuedRunError?.message}`,
      );
      throw ServerErrors.database("Failed to create run request");
    }

    // Have the queue message factory create the message to be pushed to the
    // queue
    const message = await queueMessageFactory(
      input,
      authenticatedUser,
      dataset,
      queuedRun,
    );

    // Publish the message to the queue
    const queueService = createQueueService();
    const result = await queueService.publishDataModelRun(message);

    if (!result.success) {
      logger.error(
        `Failed to publish message to queue: ${result.error?.message}`,
      );
      throw ServerErrors.queueError(
        result.error?.message || "Failed to publish to queue",
      );
    }

    logger.info(
      `Published DataModelRunRequest to queue. MessageId: ${result.messageId}`,
    );

    return {
      success: true,
      message: "Run request created successfully",
      run: queuedRun,
    };
  };
}

export const schedulerResolvers = {
  Mutation: {
    createUserModelRunRequest: genericRunRequestResolver(
      CreateUserModelRunRequestSchema,
      async (input, _user, dataset, run) => {
        const runIdBuffer = Buffer.from(run.id.replace(/-/g, ""), "hex");

        const message: DataModelRunRequest = {
          runId: new Uint8Array(runIdBuffer),
          datasetId: dataset.id,
          modelReleaseIds: input.selectedModels || [],
        };

        return message;
      },
    ),
  },
  Run: {
    datasetId: (parent: RunRow) => parent.dataset_id,
    triggerType: (parent: RunRow) =>
      parent.run_type === "manual"
        ? RunTriggerType.Manual
        : RunTriggerType.Scheduled,
    runType: (parent: RunRow) =>
      parent.run_type === "manual" ? RunType.Manual : RunType.Scheduled,
    queuedAt: (parent: RunRow) => parent.queued_at,
    status: (parent: RunRow) => mapRunStatus(parent.status),
    startedAt: (parent: RunRow) => parent.started_at,
    finishedAt: (parent: RunRow) => parent.completed_at,
    materializations: (
      parent: RunRow,
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
          eq: [{ key: "run_id", value: parent.id }],
        },
      });
    },
  },
  Materialization: {
    runId: (parent: MaterializationRow) => parent.run_id,
    // Added resolver for 'run' field
    run: async (parent: MaterializationRow) => {
      const supabase = createAdminClient();
      const { data, error } = await supabase
        .from("run")
        .select("*")
        .eq("id", parent.run_id)
        .single();
      if (error) {
        logger.error(
          `Error fetching run with id ${parent.run_id}: ${error.message}`,
        );
        throw ServerErrors.database(
          `Failed to fetch run with id ${parent.run_id}`,
        );
      }
      return data;
    },
    datasetId: (parent: MaterializationRow) => parent.dataset_id,
    createdAt: (parent: MaterializationRow) => parent.created_at,
    schema: (parent: MaterializationRow) => parent.schema,
  },
};
