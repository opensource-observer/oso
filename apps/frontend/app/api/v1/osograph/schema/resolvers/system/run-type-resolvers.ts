import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import { getUserProfile } from "@/app/api/v1/osograph/utils/auth";
import { RunRow } from "@/lib/types/schema-types";
import {
  RunStatus,
  RunTriggerType,
  RunType,
} from "@/lib/graphql/generated/graphql";
import { getSystemClient } from "@/app/api/v1/osograph/utils/access-control";
import { logger } from "@/lib/logger";
import { ServerErrors } from "@/app/api/v1/osograph/utils/errors";
import { getSignedUrl, parseGcsUrl } from "@/lib/clients/gcs";
import { assertNever } from "@opensource-observer/utils";
import { queryWithPagination } from "@/app/api/v1/osograph/utils/query-helpers";
import { FilterableConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import { StepWhereSchema } from "@/app/api/v1/osograph/utils/validation";

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

/**
 * Type resolvers for Run.
 * These field resolvers don't require auth checks as they operate on
 * already-fetched run data.
 */
export const runTypeResolvers: GraphQLResolverModule<GraphQLContext> = {
  Run: {
    datasetId: (parent: RunRow) => parent.dataset_id,
    dataset: async (
      parent: RunRow,
      _args: unknown,
      context: GraphQLContext,
    ) => {
      if (!parent.dataset_id) {
        return null;
      }
      const client = getSystemClient(context);
      const { data, error } = await client
        .from("datasets")
        .select("*")
        .eq("id", parent.dataset_id)
        .single();
      if (error) {
        logger.error(
          `Error fetching dataset with id ${parent.dataset_id}: ${error.message}`,
        );
        throw ServerErrors.database(
          `Failed to fetch dataset with id ${parent.dataset_id}`,
        );
      }
      return data;
    },
    orgId: (parent: RunRow) => parent.org_id,
    organization: async (
      parent: RunRow,
      _args: unknown,
      context: GraphQLContext,
    ) => {
      const client = getSystemClient(context);
      const { data, error } = await client
        .from("organizations")
        .select("*")
        .eq("id", parent.org_id)
        .single();
      if (error) {
        logger.error(
          `Error fetching organization with id ${parent.org_id}: ${error.message}`,
        );
        throw ServerErrors.database(
          `Failed to fetch organization with id ${parent.org_id}`,
        );
      }
      return data;
    },
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
    logsUrl: async (parent: RunRow) => {
      if (!parent.logs_url) return null;

      try {
        const parsed = parseGcsUrl(parent.logs_url);
        if (!parsed) {
          logger.warn(
            `Invalid GCS URL format for run ${parent.id}: ${parent.logs_url}`,
          );
          return parent.logs_url;
        }

        return await getSignedUrl(parsed.bucketName, parsed.fileName, 5);
      } catch (error) {
        logger.error(
          `Failed to generate signed URL for run ${parent.id}: ${error}`,
        );
        return parent.logs_url;
      }
    },
    steps: (
      parent: RunRow,
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      const client = getSystemClient(context);

      return queryWithPagination(args, context, {
        client,
        orgIds: parent.org_id,
        tableName: "step",
        whereSchema: StepWhereSchema,
        basePredicate: {
          eq: [{ key: "run_id", value: parent.id }],
        },
      });
    },
    requestedBy: async (
      parent: RunRow,
      _args: unknown,
      context: GraphQLContext,
    ) => {
      if (!parent.requested_by) {
        return null;
      }
      const client = getSystemClient(context);
      return getUserProfile(parent.requested_by, client);
    },
    metadata: (parent: RunRow) => parent.metadata,
  },
};
