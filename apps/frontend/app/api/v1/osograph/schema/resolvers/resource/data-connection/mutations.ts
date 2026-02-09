import { SupabaseAdminClient } from "@/lib/supabase/admin";
import { logger } from "@/lib/logger";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { requireAuthentication } from "@/app/api/v1/osograph/utils/auth";
import {
  ResourceErrors,
  ServerErrors,
} from "@/app/api/v1/osograph/utils/errors";
import { getTrinoAdminClient } from "@/lib/clients/trino";
import { deleteTrinoCatalog } from "@/lib/dynamic-connectors";
import { DynamicConnectorsRow } from "@/lib/types/schema-types";
import { createQueueService } from "@/lib/services/queue";
import { SyncConnectionRunRequest } from "@opensource-observer/osoprotobufs/sync-connection";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import { getOrgResourceClient } from "@/app/api/v1/osograph/utils/access-control";
import {
  MutationCreateDataConnectionArgs,
  MutationDeleteDataConnectionArgs,
  MutationSyncDataConnectionArgs,
} from "@/lib/graphql/generated/graphql";

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

/**
 * Data connection mutations that operate on existing data connection resources.
 * These resolvers use getOrgResourceClient for fine-grained permission checks.
 */
export const dataConnectionMutations: GraphQLResolverModule<GraphQLContext>["Mutation"] =
  {
    createDataConnectionAlias: async (
      _: unknown,
      { input: _input }: MutationCreateDataConnectionArgs,
      _context: GraphQLContext,
    ) => {
      throw new Error("Not implemented");
    },

    deleteDataConnectionAlias: async (
      _: unknown,
      { id: _id }: MutationDeleteDataConnectionArgs,
      _context: GraphQLContext,
    ) => {
      throw new Error("Not implemented");
    },

    deleteDataConnection: async (
      _: unknown,
      { id }: MutationDeleteDataConnectionArgs,
      context: GraphQLContext,
    ) => {
      const { client } = await getOrgResourceClient(
        context,
        "data_connection",
        id,
        "admin",
      );

      const { data: connector, error: updateError } = await client
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
        await client
          .from("dynamic_connectors")
          .update({
            deleted_at: null,
          })
          .eq("id", id);

        throw ServerErrors.externalService(
          `Error dropping catalog: ${trinoError}`,
        );
      }

      return {
        success: true,
        message: "Data connection deleted successfully",
      };
    },

    syncDataConnection: async (
      _: unknown,
      { id }: MutationSyncDataConnectionArgs,
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);

      const { client } = await getOrgResourceClient(
        context,
        "data_connection",
        id,
        "write",
      );

      const { data: dataConnection, error: fetchError } = await client
        .from("dynamic_connectors")
        .select("id, org_id")
        .eq("id", id)
        .single();

      if (fetchError || !dataConnection) {
        throw ResourceErrors.notFound("DataConnection", id);
      }

      const queuedRun = await syncDataConnection(
        client,
        authenticatedUser.userId,
        dataConnection,
      );

      return {
        success: true,
        run: queuedRun,
        message: "Data connection sync run queued successfully",
      };
    },
  };
