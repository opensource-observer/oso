import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { requireAuthentication } from "@/app/api/v1/osograph/utils/auth";
import {
  NotebookErrors,
  ServerErrors,
} from "@/app/api/v1/osograph/utils/errors";
import { putBase64Image } from "@/lib/clients/cloudflare-r2";
import { logger } from "@/lib/logger";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import {
  SaveNotebookPreviewSchema,
  UpdateNotebookSchema,
  validateBase64PngImage,
  validateInput,
} from "@/app/api/v1/osograph/utils/validation";
import { signOsoJwt } from "@/lib/auth/auth";
import { createQueueService } from "@/lib/services/queue/factory";
import { PublishNotebookRunRequest } from "@opensource-observer/osoprotobufs/publish-notebook";
import { revalidateTag } from "next/cache";
import { getOrgResourceClient } from "@/app/api/v1/osograph/utils/access-control";
import {
  MutationPublishNotebookArgs,
  MutationSaveNotebookPreviewArgs,
  MutationUnpublishNotebookArgs,
  MutationUpdateNotebookArgs,
} from "@/lib/graphql/generated/graphql";

const PREVIEWS_BUCKET = "notebook-previews";

/**
 * Notebook mutations that operate on existing notebook resources.
 * These resolvers use getOrgResourceClient for fine-grained permission checks.
 */
export const notebookMutations: GraphQLResolverModule<GraphQLContext>["Mutation"] =
  {
    updateNotebook: async (
      _: unknown,
      args: MutationUpdateNotebookArgs,
      context: GraphQLContext,
    ) => {
      const input = validateInput(UpdateNotebookSchema, args.input);

      const { client } = await getOrgResourceClient(
        context,
        "notebook",
        input.id,
        "write",
      );

      const updateData: { notebook_name?: string; description?: string } = {};
      if (input.name !== undefined) {
        updateData.notebook_name = input.name;
      }
      if (input.description !== undefined) {
        updateData.description = input.description;
      }

      const { data: updated, error } = await client
        .from("notebooks")
        .update(updateData)
        .eq("id", input.id)
        .select()
        .single();

      if (error) {
        throw ServerErrors.database(
          `Failed to update notebook: ${error.message}`,
        );
      }

      return {
        notebook: updated,
        message: "Notebook updated successfully",
        success: true,
      };
    },

    saveNotebookPreview: async (
      _: unknown,
      args: MutationSaveNotebookPreviewArgs,
      context: GraphQLContext,
    ) => {
      const input = validateInput(SaveNotebookPreviewSchema, args.input);
      validateBase64PngImage(input.preview);

      await getOrgResourceClient(
        context,
        "notebook",
        input.notebookId,
        "write",
      );

      try {
        logger.log(
          `Uploading notebook preview for ${input.notebookId} to bucket "${PREVIEWS_BUCKET}"`,
        );

        await putBase64Image(
          PREVIEWS_BUCKET,
          `${input.notebookId}.png`,
          input.preview,
        );

        logger.log(
          `Successfully saved notebook preview for ${input.notebookId}`,
        );

        return {
          success: true,
          message: "Notebook preview saved successfully",
        };
      } catch (error) {
        logger.error(
          `Failed to save notebook preview for ${input.notebookId}: ${error}`,
        );
        throw ServerErrors.storage("Failed to save notebook preview");
      }
    },

    publishNotebook: async (
      _: unknown,
      args: MutationPublishNotebookArgs,
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const { notebookId } = args;

      const { client } = await getOrgResourceClient(
        context,
        "notebook",
        notebookId,
        "admin",
      );

      const { data: notebook } = await client
        .from("notebooks")
        .select("id, organizations!inner(id, org_name)")
        .eq("id", notebookId)
        .single();

      if (!notebook) {
        throw NotebookErrors.notFound();
      }

      const osoToken = await signOsoJwt(authenticatedUser, {
        orgId: notebook.organizations.id,
        orgName: notebook.organizations.org_name,
      });

      const { data: queuedRun, error: queuedRunError } = await client
        .from("run")
        .insert({
          org_id: notebook.organizations.id,
          run_type: "manual",
          requested_by: authenticatedUser.userId,
          metadata: {
            notebookId: notebook.id,
          },
        })
        .select()
        .single();
      if (queuedRunError || !queuedRun) {
        logger.error(
          `Error creating run for notebook ${notebook.id}: ${queuedRunError?.message}`,
        );
        throw ServerErrors.database("Failed to create run request");
      }

      const queueService = createQueueService();

      const runIdBuffer = Buffer.from(queuedRun.id.replace(/-/g, ""), "hex");
      const publishMessage: PublishNotebookRunRequest = {
        runId: new Uint8Array(runIdBuffer),
        notebookId: notebook.id,
        osoApiKey: osoToken,
      };

      const result = await queueService.queueMessage({
        queueName: "publish_notebook_run_requests",
        message: publishMessage,
        encoder: PublishNotebookRunRequest,
      });
      if (!result.success) {
        logger.error(
          `Failed to publish message to queue: ${result.error?.message}`,
        );
        throw ServerErrors.queueError(
          result.error?.message || "Failed to publish to queue",
        );
      }

      return {
        success: true,
        run: queuedRun,
        message: "Notebook publish run queued successfully",
      };
    },

    unpublishNotebook: async (
      _: unknown,
      args: MutationUnpublishNotebookArgs,
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const { notebookId } = args;

      const { client } = await getOrgResourceClient(
        context,
        "notebook",
        notebookId,
        "admin",
      );

      const { data: publishedNotebook, error } = await client
        .from("published_notebooks")
        .select("*")
        .eq("notebook_id", notebookId)
        .single();
      if (error) {
        logger.log("Failed to find published notebook:", error);
        throw NotebookErrors.notFound();
      }
      const { error: deleteError } = await client.storage
        .from("published-notebooks")
        .remove([publishedNotebook.data_path]);
      if (deleteError) {
        logger.log("Failed to delete notebook file:", deleteError);
        throw ServerErrors.database("Failed to delete notebook file");
      }
      const { error: updateError } = await client
        .from("published_notebooks")
        .update({
          deleted_at: new Date().toISOString(),
          updated_by: authenticatedUser.userId,
        })
        .eq("id", publishedNotebook.id);
      if (updateError) {
        logger.log("Failed to delete notebook file:", updateError);
        throw ServerErrors.database("Failed to delete notebook file");
      }

      revalidateTag(publishedNotebook.id);
      return {
        success: true,
        message: "Notebook unpublished successfully",
      };
    },
  };
