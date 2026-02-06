import { createAdminClient, SupabaseAdminClient } from "@/lib/supabase/admin";
import { logger } from "@/lib/logger";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import {
  getOrganization,
  requireAuthentication,
  requireOrgMembership,
} from "@/app/api/v1/osograph/utils/auth";
import {
  OrganizationErrors,
  ResourceErrors,
  ServerErrors,
} from "@/app/api/v1/osograph/utils/errors";
import {
  CreateDataConnectionSchema,
  validateInput,
  DataConnectionWhereSchema,
} from "@/app/api/v1/osograph/utils/validation";
import { z } from "zod";
import { getTrinoAdminClient } from "@/lib/clients/trino";
import {
  createTrinoCatalog,
  deleteTrinoCatalog,
  validateDynamicConnector,
} from "@/lib/dynamic-connectors";
import {
  DataConnectionAliasRow,
  DynamicConnectorsRow,
} from "@/lib/types/schema-types";
import { createQueueService } from "@/lib/services/queue";
import { queryWithPagination } from "@/app/api/v1/osograph/utils/query-helpers";
import { FilterableConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import { SyncConnectionRunRequest } from "@opensource-observer/osoprotobufs/sync-connection";
import { getMaterializations } from "@/app/api/v1/osograph/utils/resolver-helpers";
import { getModelContext } from "@/app/api/v1/osograph/schema/resolvers/model-context";
import {
  checkMaterializationExists,
  executePreviewQuery,
  generateTableId,
} from "@/app/api/v1/osograph/utils/model";

async function syncDataConnection(
  supabase: SupabaseAdminClient,
  userId: string,
  dataConnection: Pick<DynamicConnectorsRow, "id" | "org_id">,
) {
  const { data: queuedRun, error: queuedRunError } = await supabase
    .from("run")
    .insert({
      org_id: dataConnection.org_id,
      run_type: "manual",
      requested_by: userId,
      metadata: {
        dataConnectionId: dataConnection.id,
      },
    })
    .select()
    .single();
  if (queuedRunError || !queuedRun) {
    logger.error(
      `Error creating run for data connection ${dataConnection.id}: ${queuedRunError?.message}`,
    );
    throw ServerErrors.database("Failed to create run request");
  }

  const queueService = createQueueService();

  const runIdBuffer = Buffer.from(queuedRun.id.replace(/-/g, ""), "hex");
  const publishMessage: SyncConnectionRunRequest = {
    runId: new Uint8Array(runIdBuffer),
    connectionId: dataConnection.id,
  };

  const result = await queueService.queueMessage({
    queueName: "sync_connection_run_requests",
    message: publishMessage,
    encoder: SyncConnectionRunRequest,
  });
  if (!result.success) {
    logger.error(
      `Failed to publish message to queue: ${result.error?.message}`,
    );
    throw ServerErrors.queueError(
      result.error?.message || "Failed to publish to queue",
    );
  }
  return queuedRun;
}

export const dataConnectionResolvers = {
  Query: {
    dataConnections: async (
      _: unknown,
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      return queryWithPagination(args, context, {
        tableName: "dynamic_connectors",
        whereSchema: DataConnectionWhereSchema,
        requireAuth: true,
        filterByUserOrgs: true,
        basePredicate: {
          is: [{ key: "deleted_at", value: null }],
        },
      });
    },
  },
  Mutation: {
    createDataConnection: async (
      _: unknown,
      {
        input,
      }: {
        input: z.infer<typeof CreateDataConnectionSchema>;
      },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const { orgId, name, type, config, credentials } = validateInput(
        CreateDataConnectionSchema,
        input,
      );

      await requireOrgMembership(authenticatedUser.userId, orgId);

      const supabase = createAdminClient();
      const { data: org, error: orgError } = await supabase
        .from("organizations")
        .select()
        .eq("id", orgId)
        .single();
      if (orgError || !org) {
        throw OrganizationErrors.notFound();
      }
      validateDynamicConnector(name, type, org.org_name);

      const { data, error } = await supabase
        .from("dynamic_connectors")
        .insert({
          org_id: orgId,
          connector_name: name,
          connector_type: type,
          config: config,
          created_by: authenticatedUser.userId,
        })
        .select()
        .single();

      if (error) {
        logger.error("Failed to create data connection:", error);
        throw ServerErrors.database("Failed to create data connection");
      }

      const trinoClient = getTrinoAdminClient();
      const { error: trinoError } = await createTrinoCatalog(
        trinoClient,
        data,
        credentials,
      );
      if (trinoError) {
        // Best effort try to cleanup the connector from supabase
        await supabase.from("dynamic_connectors").delete().eq("id", data.id);
        throw ServerErrors.externalService(
          `Error creating catalog: ${trinoError}`,
        );
      }

      await syncDataConnection(supabase, authenticatedUser.userId, data);

      return {
        success: true,
        message: "Data connection created successfully",
        dataConnection: data,
      };
    },

    deleteDataConnection: async (
      _: unknown,
      { id }: { id: string },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const supabase = createAdminClient();

      const { data: dataConnection, error: fetchError } = await supabase
        .from("dynamic_connectors")
        .select("org_id")
        .eq("id", id)
        .single();

      if (fetchError || !dataConnection) {
        throw ResourceErrors.notFound("DataConnection", id);
      }

      await requireOrgMembership(
        authenticatedUser.userId,
        dataConnection.org_id,
      );

      const { data: connector, error: updateError } = await supabase
        .from("dynamic_connectors")
        .update({
          deleted_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        })
        .eq("id", id)
        .select()
        .single();

      if (updateError || !connector) {
        logger.error("Failed to delete data connection:", updateError);
        throw ServerErrors.database(
          `Failed to delete data connection: ${updateError.message}`,
        );
      }

      const trinoClient = getTrinoAdminClient();
      const { error: trinoError } = await deleteTrinoCatalog(
        trinoClient,
        connector,
      );

      if (trinoError) {
        // Best effort reverting operation
        await supabase
          .from("dynamic_connectors")
          .update({
            deleted_at: null,
          })
          .eq("id", id);

        throw ServerErrors.externalService(
          `Error dropping catalog: ${trinoError}`,
        );
      }

      const { data: datasets, error } = await supabase
        .from("data_connection_alias")
        .select("id, datasets(id)")
        .eq("data_connection_id", id);
      if (error) {
        logger.error("Failed to delete datasets:", error);
        throw ServerErrors.database(
          `Failed to delete datasets: ${error.message}`,
        );
      }
      const { error: deleteError } = await supabase
        .from("datasets")
        .delete()
        .in(
          "id",
          datasets.map((d) => d.datasets.id),
        );
      if (deleteError) {
        logger.error("Failed to delete datasets:", deleteError);
        throw ServerErrors.database(
          `Failed to delete datasets: ${deleteError.message}`,
        );
      }

      return {
        success: true,
        message: "Data connection deleted successfully",
      };
    },

    syncDataConnection: async (
      _: unknown,
      { id }: { id: string },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const supabase = createAdminClient();

      const { data: dataConnection, error: fetchError } = await supabase
        .from("dynamic_connectors")
        .select("id, org_id")
        .eq("id", id)
        .single();

      if (fetchError || !dataConnection) {
        throw ResourceErrors.notFound("DataConnection", id);
      }

      await requireOrgMembership(
        authenticatedUser.userId,
        dataConnection.org_id,
      );

      const queuedRun = await syncDataConnection(
        supabase,
        authenticatedUser.userId,
        dataConnection,
      );

      return {
        success: true,
        run: queuedRun,
        message: "Data connection sync run queued successfully",
      };
    },
  },

  DataConnection: {
    orgId: (parent: DynamicConnectorsRow) => parent.org_id,
    organization: (parent: DynamicConnectorsRow) => {
      return getOrganization(parent.org_id);
    },
    createdAt: (parent: DynamicConnectorsRow) => parent.created_at,
    updatedAt: (parent: DynamicConnectorsRow) => parent.updated_at,
    name: (parent: DynamicConnectorsRow) => parent.connector_name,
    type: (parent: DynamicConnectorsRow) => parent.connector_type.toUpperCase(),
  },

  DataConnectionAlias: {
    orgId: (parent: DataConnectionAliasRow) => parent.org_id,
    datasetId: (parent: DataConnectionAliasRow) => parent.dataset_id,
    schema: (parent: DataConnectionAliasRow) => parent.schema_name,
    dataConnectionId: (parent: DataConnectionAliasRow) =>
      parent.data_connection_id,
    createdAt: (parent: DataConnectionAliasRow) => parent.created_at,
    updatedAt: (parent: DataConnectionAliasRow) => parent.updated_at,
    modelContext: async (
      parent: DataConnectionAliasRow,
      args: { tableName: string },
    ) => {
      return getModelContext(parent.dataset_id, args.tableName);
    },
    materializations: async (
      parent: DataConnectionAliasRow,
      args: FilterableConnectionArgs & { tableName: string },
      context: GraphQLContext,
    ) => {
      const { tableName, ...restArgs } = args;
      return getMaterializations(
        restArgs,
        context,
        parent.org_id,
        parent.dataset_id,
        generateTableId("DATA_CONNECTION", tableName),
      );
    },
    previewData: async (
      parent: DataConnectionAliasRow,
      args: { tableName: string },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);

      const tableId = generateTableId("DATA_CONNECTION", args.tableName);

      const materializationExists = await checkMaterializationExists(
        parent.org_id,
        parent.dataset_id,
        tableId,
      );
      if (!materializationExists) {
        return [];
      }

      return executePreviewQuery(
        parent.org_id,
        parent.dataset_id,
        tableId,
        authenticatedUser,
        args.tableName,
      );
    },
  },
};
