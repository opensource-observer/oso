import { getOrgScopedClient } from "@/app/api/v1/osograph/utils/access-control";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import { MaterializationWhereSchema } from "@/app/api/v1/osograph/utils/validation";
import { MaterializationRow, StepRow } from "@/lib/types/schema-types";
import { logger } from "@/lib/logger";
import { ServerErrors } from "@/app/api/v1/osograph/utils/errors";
import { StepStatus } from "@/lib/graphql/generated/graphql";
import { assertNever } from "@opensource-observer/utils";
import { queryWithPagination } from "@/app/api/v1/osograph/utils/query-helpers";
import { FilterableConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import { getSignedUrl, parseGcsUrl } from "@/lib/clients/gcs";

/**
 * Type resolvers for organization-scoped resources.
 * These resolvers use organization-scoped authentication - users must be
 * members of the organization that owns the resource to access these fields.
 */
export const organizationTypeResolvers: GraphQLResolverModule<GraphQLContext> =
  {
    Materialization: {
      runId: (parent: MaterializationRow) => parent.run_id,
      run: async (
        parent: MaterializationRow,
        _args: unknown,
        context: GraphQLContext,
      ) => {
        const { client } = await getOrgScopedClient(context, parent.org_id);
        const { data, error } = await client
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

    Step: {
      runId: (parent: StepRow) => parent.run_id,
      run: async (parent: StepRow, _args: unknown, context: GraphQLContext) => {
        const { client } = await getOrgScopedClient(context, parent.org_id);
        const { data, error } = await client
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
      name: (parent: StepRow) => parent.name,
      displayName: (parent: StepRow) => parent.display_name,
      logsUrl: async (parent: StepRow) => {
        if (!parent.logs_url) return "";

        try {
          const parsed = parseGcsUrl(parent.logs_url);
          if (!parsed) {
            logger.warn(
              `Invalid GCS URL format for step ${parent.id}: ${parent.logs_url}`,
            );
            return parent.logs_url;
          }

          return await getSignedUrl(parsed.bucketName, parsed.fileName, 5);
        } catch (error) {
          logger.error(
            `Failed to generate signed URL for step ${parent.id}: ${error}`,
          );
          return parent.logs_url;
        }
      },
      startedAt: (parent: StepRow) => parent.started_at,
      finishedAt: (parent: StepRow) => parent.completed_at,
      status: (parent: StepRow) => {
        switch (parent.status) {
          case "running":
            return StepStatus.Running;
          case "failed":
            return StepStatus.Failed;
          case "canceled":
            return StepStatus.Canceled;
          case "success":
            return StepStatus.Success;
          default:
            assertNever(parent.status, `Unknown step status: ${parent.status}`);
        }
      },
      materializations: async (
        parent: StepRow,
        args: FilterableConnectionArgs,
        context: GraphQLContext,
      ) => {
        const { client } = await getOrgScopedClient(context, parent.org_id);

        return queryWithPagination(args, context, {
          client,
          orgIds: parent.org_id,
          tableName: "materialization",
          whereSchema: MaterializationWhereSchema,
          basePredicate: {
            eq: [{ key: "step_id", value: parent.id }],
          },
        });
      },
    },
  };
