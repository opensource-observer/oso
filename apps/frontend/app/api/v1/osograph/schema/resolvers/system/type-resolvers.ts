import { getSystemClient } from "@/app/api/v1/osograph/utils/access-control";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import { Table } from "@/lib/types/table";
import { LegacyInferredTableResolver } from "@/lib/query/resolvers/legacy-table-resolver";
import { DBTableResolver } from "@/lib/query/resolvers/db-table-resolver";
import { TableResolutionMap } from "@/lib/query/resolver";
import { MetadataInferredTableResolver } from "@/lib/query/resolvers/metadata-table-resolver";
import {
  ResolveTablesSchema,
  validateInput,
  MaterializationWhereSchema,
} from "@/app/api/v1/osograph/utils/validation";
import { MaterializationRow, StepRow } from "@/lib/types/schema-types";
import { logger } from "@/lib/logger";
import { ServerErrors } from "@/app/api/v1/osograph/utils/errors";
import { StepStatus } from "@/lib/graphql/generated/graphql";
import { assertNever } from "@opensource-observer/utils";
import { queryWithPagination } from "@/app/api/v1/osograph/utils/query-helpers";
import { FilterableConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import { getSignedUrl, parseGcsUrl } from "@/lib/clients/gcs";

export const systemTypeResolvers: GraphQLResolverModule<GraphQLContext> = {
  System: {
    resolveTables: async (
      _: unknown,
      // TODO(jabolo): Reconcile this input with a type from @/lib/graphql/generated/graphql
      // eslint-disable-next-line oso-frontend/type-safety/no-inline-resolver-types
      input: {
        references: string[];
        metadata?: { orgName?: string; datasetName?: string };
      },
      context: GraphQLContext,
    ) => {
      const client = getSystemClient(context);

      const { references, metadata } = validateInput(
        ResolveTablesSchema,
        input,
      );

      const tableResolvers = [
        new LegacyInferredTableResolver(),
        new MetadataInferredTableResolver(),
        new DBTableResolver(client, [
          (table) => {
            // If the catalog is iceberg return the table as is
            if (table.catalog === "iceberg") {
              return table;
            }
            return null;
          },
          (table) => {
            // If the catalog has a double underscore in the name we assume it's a
            // legacy private connector catalog and return the table as is
            if (table.catalog.includes("__")) {
              return table;
            }
            return null;
          },
        ]),
      ];

      let tableResolutionMap: TableResolutionMap = {};
      for (const ref of references) {
        tableResolutionMap[ref] = Table.fromString(ref);
      }

      for (const resolver of tableResolvers) {
        tableResolutionMap = await resolver.resolveTables(tableResolutionMap, {
          orgName: metadata?.orgName,
          datasetName: metadata?.datasetName,
        });
      }

      const results = Object.entries(tableResolutionMap).map(
        ([ref, table]) => ({
          reference: ref,
          fqn: table.toFQN(),
        }),
      );

      return results;
    },
  },

  Materialization: {
    runId: (parent: MaterializationRow) => parent.run_id,
    run: async (
      parent: MaterializationRow,
      _args: unknown,
      context: GraphQLContext,
    ) => {
      const client = getSystemClient(context);
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
      const client = getSystemClient(context);
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
    materializations: (
      parent: StepRow,
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      // TODO(jabolo): Handle special case where the caller does
      // not pass `orgIds` as `system`. In the new implementation,
      // it will fail and return and empty connection as of now.
      const _client = getSystemClient(context);

      // eslint-disable-next-line @typescript-eslint/no-deprecated
      return queryWithPagination(args, context, {
        tableName: "materialization",
        whereSchema: MaterializationWhereSchema,
        requireAuth: false,
        filterByUserOrgs: false,
        parentOrgIds: parent.org_id,
        basePredicate: {
          eq: [{ key: "step_id", value: parent.id }],
        },
      });
    },
  },
};
