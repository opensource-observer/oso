import { createAdminClient } from "@/lib/supabase/admin";
import type { GraphQLResolverModule } from "@/app/api/v1/osograph/utils/types";
import {
  requireAuthentication,
  requireOrgMembership,
  getOrganizationByName,
  getOrganization,
  type GraphQLContext,
} from "@/app/api/v1/osograph/utils/auth";
import {
  ServerErrors,
  NotebookErrors,
  OrganizationErrors,
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
    osoApp_notebooks: async (
      _: unknown,
      args: { orgName?: string },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const supabase = createAdminClient();

      let query = supabase
        .from("notebooks")
        .select(
          "id, notebook_name, description, created_at, updated_at, org_id",
        )
        .is("deleted_at", null);

      if (args.orgName) {
        const org = await getOrganizationByName(args.orgName);
        if (!org) {
          throw OrganizationErrors.notFound();
        }
        await requireOrgMembership(authenticatedUser.userId, org.id);
        query = query.eq("org_id", org.id);
      } else {
        const { data: memberships } = await supabase
          .from("users_by_organization")
          .select("org_id")
          .eq("user_id", authenticatedUser.userId)
          .is("deleted_at", null);

        const orgIds = memberships?.map((m) => m.org_id) || [];
        if (orgIds.length === 0) {
          return [];
        }
        query = query.in("org_id", orgIds);
      }

      const { data: notebooks, error } = await query;

      if (error) {
        logger.error(`Failed to fetch notebooks: ${error}`);
        throw ServerErrors.database("Failed to fetch notebooks");
      }

      return notebooks || [];
    },

    osoApp_notebook: async (
      _: unknown,
      args: { notebookId: string },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const supabase = createAdminClient();

      const { data: notebook, error } = await supabase
        .from("notebooks")
        .select(
          "id, notebook_name, description, created_at, updated_at, org_id",
        )
        .eq("id", args.notebookId)
        .is("deleted_at", null)
        .single();

      if (error || !notebook) {
        throw NotebookErrors.notFound();
      }

      await requireOrgMembership(authenticatedUser.userId, notebook.org_id);

      return notebook;
    },
  },

  Mutation: {
    osoApp_saveNotebookPreview: async (
      _: unknown,
      args: {
        input: {
          notebookId: string;
          orgName: string;
          previewImage: string;
        };
      },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const { notebookId, orgName, previewImage } = args.input;

      const org = await getOrganizationByName(orgName);
      if (!org) {
        throw OrganizationErrors.notFound();
      }

      await requireOrgMembership(authenticatedUser.userId, org.id);

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

  Notebook: {
    __resolveReference: async (reference: { id: string }) => {
      const supabase = createAdminClient();
      const { data } = await supabase
        .from("notebooks")
        .select(
          "id, notebook_name, description, created_at, updated_at, org_id",
        )
        .eq("id", reference.id)
        .is("deleted_at", null)
        .single();
      return data;
    },

    notebookName: (parent: { notebook_name: string }) => parent.notebook_name,
    createdAt: (parent: { created_at: string }) => parent.created_at,
    updatedAt: (parent: { updated_at: string }) => parent.updated_at,
    organization: (parent: { org_id: string }) =>
      getOrganization(parent.org_id),

    preview: async (parent: { id: string }) => {
      try {
        const objectKey = `${parent.id}.png`;
        const signedUrl = await getPreviewSignedUrl(
          PREVIEWS_BUCKET,
          objectKey,
          SIGNED_URL_EXPIRY,
        );

        return {
          notebookId: parent.id,
          signedUrl,
          expiresAt: new Date(Date.now() + SIGNED_URL_EXPIRY * 1000),
        };
      } catch (error) {
        logger.error(
          `Failed to generate preview URL for notebook ${parent.id}: ${error}`,
        );
        return null;
      }
    },
  },
};
