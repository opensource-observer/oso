import { v4 as uuidv4 } from "uuid";
import { createAdminClient } from "@/lib/supabase/admin";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import {
  getOrganization,
  getUserProfile,
  requireAuthentication,
  requireOrgMembership,
} from "@/app/api/v1/osograph/utils/auth";
import {
  NotebookErrors,
  ServerErrors,
} from "@/app/api/v1/osograph/utils/errors";
import {
  getPreviewSignedUrl,
  putBase64Image,
} from "@/lib/clients/cloudflare-r2";
import { logger } from "@/lib/logger";
import type { FilterableConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import { requireOrganizationAccess } from "@/app/api/v1/osograph/utils/resolver-helpers";
import {
  CreateNotebookSchema,
  NotebookWhereSchema,
  SaveNotebookPreviewSchema,
  UpdateNotebookSchema,
  validateBase64PngImage,
  validateInput,
} from "@/app/api/v1/osograph/utils/validation";
import { queryWithPagination } from "@/app/api/v1/osograph/utils/query-helpers";

const PREVIEWS_BUCKET = "notebook-previews";
const SIGNED_URL_EXPIRY = 900;

export const notebookResolvers: GraphQLResolverModule<GraphQLContext> = {
  Query: {
    notebooks: async (
      _: unknown,
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      return queryWithPagination(args, context, {
        tableName: "notebooks",
        whereSchema: NotebookWhereSchema,
        requireAuth: true,
        filterByUserOrgs: true,
        basePredicate: {
          is: [{ key: "deleted_at", value: null }],
        },
      });
    },
  },

  Mutation: {
    createNotebook: async (
      _: unknown,
      args: { input: { orgId: string; name: string; description?: string } },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const input = validateInput(CreateNotebookSchema, args.input);

      const supabase = createAdminClient();
      await requireOrganizationAccess(authenticatedUser.userId, input.orgId);

      const notebookId = uuidv4();
      const { data: notebook, error } = await supabase
        .from("notebooks")
        .insert({
          id: notebookId,
          org_id: input.orgId,
          notebook_name: input.name,
          description: input.description,
          created_by: authenticatedUser.userId,
        })
        .select()
        .single();

      if (error) {
        throw ServerErrors.database(
          `Failed to create notebook: ${error.message}`,
        );
      }

      return {
        notebook,
        message: "Notebook created successfully",
        success: true,
      };
    },

    updateNotebook: async (
      _: unknown,
      args: { input: { id: string; name?: string; description?: string } },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const input = validateInput(UpdateNotebookSchema, args.input);

      const supabase = createAdminClient();
      const { data: notebook, error: fetchError } = await supabase
        .from("notebooks")
        .select("org_id")
        .eq("id", input.id)
        .single();

      if (fetchError || !notebook) {
        throw NotebookErrors.notFound();
      }

      await requireOrgMembership(authenticatedUser.userId, notebook.org_id);

      const updateData: { notebook_name?: string; description?: string } = {};
      if (input.name !== undefined) {
        updateData.notebook_name = input.name;
      }
      if (input.description !== undefined) {
        updateData.description = input.description;
      }

      const { data: updated, error } = await supabase
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
      args: { input: { notebookId: string; preview: string } },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const input = validateInput(SaveNotebookPreviewSchema, args.input);
      validateBase64PngImage(input.preview);

      const supabase = createAdminClient();
      const { data: notebook } = await supabase
        .from("notebooks")
        .select("org_id")
        .eq("id", input.notebookId)
        .single();

      if (!notebook) {
        throw NotebookErrors.notFound();
      }

      await requireOrgMembership(authenticatedUser.userId, notebook.org_id);

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
  },

  Notebook: {
    name: (parent: { notebook_name: string }) => parent.notebook_name,
    createdAt: (parent: { created_at: string }) => parent.created_at,
    updatedAt: (parent: { updated_at: string }) => parent.updated_at,
    creatorId: (parent: { created_by: string }) => parent.created_by,
    orgId: (parent: { org_id: string }) => parent.org_id,

    creator: async (parent: { created_by: string }) => {
      return getUserProfile(parent.created_by);
    },

    organization: async (parent: { org_id: string }) => {
      return getOrganization(parent.org_id);
    },

    preview: async (parent: { id: string }) => {
      try {
        const objectKey = `${parent.id}.png`;
        const signedUrl = await getPreviewSignedUrl(
          PREVIEWS_BUCKET,
          objectKey,
          SIGNED_URL_EXPIRY,
        );

        return signedUrl;
      } catch (error) {
        logger.error(
          `Failed to generate preview URL for notebook ${parent.id}: ${error}`,
        );
        return null;
      }
    },
  },
};
