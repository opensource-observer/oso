import { MaterializationRow, RunRow } from "@/lib/types/schema-types";
import { RunStatus } from "@/lib/graphql/generated/graphql";
import { queryWithPagination } from "@/app/api/v1/osograph/utils/query-helpers";
import { FilterableConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import {
  CreateRunRequestSchema,
  MaterializationWhereSchema,
  validateInput,
} from "@/app/api/v1/osograph/utils/validation";
import { assertNever } from "@opensource-observer/utils";
import { logger } from "@/lib/logger";
import { createAdminClient } from "@/lib/supabase/admin";
import {
  ServerErrors,
  ResourceErrors,
} from "@/app/api/v1/osograph/utils/errors";
import z from "zod";
import { requireAuthentication } from "@/app/api/v1/osograph/utils/auth";

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
    default:
      assertNever(status, `Unknown run status: ${status}`);
  }
}

export const schedulerResolvers = {
  Mutation: {
    createRunRequest: async (
      _: any,
      args: { input: z.infer<typeof CreateRunRequestSchema> },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const { definitionId, definitionType } = validateInput(
        CreateRunRequestSchema,
        args.input,
      );
      const supabase = createAdminClient();

      const getRunDefinition = async () => {
        switch (definitionType) {
          case "USER_MODEL": {
            const { data: model, error: modelError } = await supabase
              .from("model")
              .select("*")
              .eq("id", definitionId)
              .single();

            if (modelError || !model) {
              logger.error(
                `Error fetching model ${definitionId}: ${modelError?.message}`,
              );
              throw ResourceErrors.notFound("Model", definitionId);
            }
            return model;
          }
          case "DATA_INGESTION":
          case "DATA_CONNECTOR":
            throw new Error("Not implemented yet");
          default:
            assertNever(
              definitionType,
              `Unsupported definition type: ${definitionType}`,
            );
        }
      };

      const runDefinition = await getRunDefinition();

      const { data: runRequest, error: runRequestError } = await supabase
        .from("run_request")
        .insert({
          dataset_id: runDefinition.dataset_id,
          org_id: runDefinition.org_id,
          created_by: authenticatedUser.userId,
          definition_id: definitionId,
        })
        .select("*")
        .single();

      if (runRequestError || !runRequest) {
        logger.error(`Error creating run request: ${runRequestError?.message}`);
        throw ServerErrors.database("Failed to create run request");
      }

      return {
        success: true,
        message: "Run request created successfully",
        runRequest: {
          id: runRequest.id,
          requestedAt: runRequest.created_at,
          definition: runDefinition,
          requestedByUserId: authenticatedUser.userId,
          requestedBy: authenticatedUser,
        },
      };
    },
  },
  Run: {
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
