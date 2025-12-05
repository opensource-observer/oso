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
import { ServerErrors, UserErrors } from "@/app/api/v1/osograph/utils/errors";
import z from "zod";
import { requireAuthentication } from "@/app/api/v1/osograph/utils/auth";
import { AuthOrgUserSchema } from "@/lib/types/user";

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

export const schedulerResolvers = {
  Mutation: {
    createRunRequest: async (
      _: any,
      args: { input: z.infer<typeof CreateRunRequestSchema> },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const { datasetId } = validateInput(CreateRunRequestSchema, args.input);
      const supabase = createAdminClient();
      const parsedOrgUser = AuthOrgUserSchema.safeParse(authenticatedUser);
      if (!parsedOrgUser.success) {
        throw UserErrors.profileNotFound();
      }
      const orgUser = parsedOrgUser.data;

      // Create a run to store the results of the run request
      const { data: queuedRun, error: queuedRunError } = await supabase
        .from("run")
        .insert({
          org_id: orgUser.orgId,
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

      // At this point we should publish a message to the queue for processing
      // the given run request. Run Requests have different messages on a per
      // dataset type basis.

      return {
        success: true,
        message: "Run request created successfully",
        run: queuedRun,
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
