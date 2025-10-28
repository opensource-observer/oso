import { createAdminClient } from "@/lib/supabase/admin";
import type { GraphQLResolverModule } from "@/app/api/v1/osograph/utils/types";
import {
  requireAuthentication,
  requireOrgMembership,
  type GraphQLContext,
} from "@/app/api/v1/osograph/utils/auth";
import {
  ServerErrors,
  NotebookErrors,
} from "@/app/api/v1/osograph/utils/errors";
import { validateBase64PngImage } from "@/app/api/v1/osograph/utils/validation";
import {
  putBase64Image,
  getPreviewSignedUrl,
} from "@/lib/clients/cloudflare-r2";
import { logger } from "@/lib/logger";

const PREVIEWS_BUCKET = "notebook-previews";
const SIGNED_URL_EXPIRY = 900;

export const notebookResolvers: GraphQLResolverModule<GraphQLContext> = {
  Query: {
    osoApp_notebookPreview: async (
      _: unknown,
      args: { notebookId: string },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const supabase = createAdminClient();

      const { data: notebook, error } = await supabase
        .from("notebooks")
        .select("id, org_id")
        .eq("id", args.notebookId)
        .single();

      if (error || !notebook) {
        throw NotebookErrors.notFound();
      }

      await requireOrgMembership(authenticatedUser.userId, notebook.org_id);

      try {
        const objectKey = `${args.notebookId}.png`;
        logger.log(
          `Generating preview URL for notebook ${args.notebookId} from bucket "${PREVIEWS_BUCKET}" with key "${objectKey}"`,
        );

        const signedUrl = await getPreviewSignedUrl(
          PREVIEWS_BUCKET,
          objectKey,
          SIGNED_URL_EXPIRY,
        );

        const expiresAt = new Date(Date.now() + SIGNED_URL_EXPIRY * 1000);

        const response = {
          notebookId: args.notebookId,
          signedUrl,
          expiresAt,
        };

        logger.log(
          `Successfully generated preview URL for notebook ${args.notebookId}. URL expires at ${expiresAt.toISOString()}`,
        );

        return response;
      } catch (error) {
        logger.error(
          `Failed to generate preview URL for notebook ${args.notebookId}: ${error}`,
        );
        throw ServerErrors.storage("Failed to generate preview URL");
      }
    },
  },

  Mutation: {
    osoApp_saveNotebookPreview: async (
      _: unknown,
      args: {
        input: {
          notebookId: string;
          previewImage: string;
        };
      },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const supabase = createAdminClient();
      const { notebookId, previewImage } = args.input;

      const { data: notebook, error } = await supabase
        .from("notebooks")
        .select("id, org_id")
        .eq("id", notebookId)
        .single();

      if (error || !notebook) {
        throw NotebookErrors.notFound();
      }

      await requireOrgMembership(authenticatedUser.userId, notebook.org_id);

      try {
        logger.log(`Validating base64 PNG image for notebook ${notebookId}`);
        validateBase64PngImage(previewImage);

        const objectKey = `${notebookId}.png`;
        logger.log(
          `Uploading notebook preview for ${notebookId} to bucket "${PREVIEWS_BUCKET}" with key "${objectKey}". Image size: ${previewImage.length} bytes`,
        );

        await putBase64Image(PREVIEWS_BUCKET, objectKey, previewImage);

        const response = {
          success: true,
          message: "Notebook preview saved successfully",
        };

        logger.log(
          `Successfully saved notebook preview for ${notebookId} to bucket "${PREVIEWS_BUCKET}"`,
        );

        return response;
      } catch (error) {
        logger.error(
          `Failed to save notebook preview for notebook ${notebookId}: ${error}`,
        );
        throw ServerErrors.storage("Failed to save notebook preview");
      }
    },
  },
};
