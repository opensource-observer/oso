import { MaterializationRow, RunRow } from "@/lib/types/schema-types";
import { RunStatus } from "@/lib/graphql/generated/graphql";
import { queryWithPagination } from "@/app/api/v1/osograph/utils/query-helpers";
import { FilterableConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { MaterializationWhereSchema } from "@/app/api/v1/osograph/utils/validation";
import { assertNever } from "@opensource-observer/utils";
import { logger } from "@/lib/logger";
import { createAdminClient } from "@/lib/supabase/admin";
import { ServerErrors } from "@/app/api/v1/osograph/utils/errors";

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
