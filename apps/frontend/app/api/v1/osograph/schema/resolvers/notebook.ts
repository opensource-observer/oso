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
  ResourceErrors,
  ServerErrors,
} from "@/app/api/v1/osograph/utils/errors";
import {
  getPreviewSignedUrl,
  putBase64Image,
} from "@/lib/clients/cloudflare-r2";
import { logger } from "@/lib/logger";
import {
  buildConnection,
  emptyConnection,
} from "@/app/api/v1/osograph/utils/connection";
import type { ConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import {
  getFetchLimit,
  getSupabaseRange,
} from "@/app/api/v1/osograph/utils/pagination";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";

const PREVIEWS_BUCKET = "notebook-previews";
const SIGNED_URL_EXPIRY = 900;

export const notebookResolvers: GraphQLResolverModule<GraphQLContext> = {
  Query: {
    notebooks: async (
      _: unknown,
      args: ConnectionArgs,
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const supabase = createAdminClient();

      const { data: memberships } = await supabase
        .from("users_by_organization")
        .select("org_id")
        .eq("user_id", authenticatedUser.userId)
        .is("deleted_at", null);

      const orgIds = memberships?.map((m) => m.org_id) || [];
      if (orgIds.length === 0) {
        return emptyConnection();
      }

      const limit = getFetchLimit(args);
      const [start, end] = getSupabaseRange({
        ...args,
        first: limit,
      });

      const { data: notebooks, error } = await supabase
        .from("notebooks")
        .select("*")
        .in("org_id", orgIds)
        .is("deleted_at", null)
        .range(start, end);

      if (error) {
        logger.error(`Failed to fetch notebooks: ${error}`);
        throw ServerErrors.database("Failed to fetch notebooks");
      }

      if (!notebooks || notebooks.length === 0) {
        return emptyConnection();
      }

      return buildConnection(notebooks, args);
    },

    notebook: async (
      _: unknown,
      args: { id?: string; name?: string },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const supabase = createAdminClient();

      if (!args.id && !args.name) {
        return null;
      }

      let query = supabase.from("notebooks").select("*").is("deleted_at", null);

      if (args.id) {
        query = query.eq("id", args.id);
      } else if (args.name) {
        query = query.eq("name", args.name);
      }

      const { data: notebook, error } = await query.single();

      if (error || !notebook) {
        return null;
      }

      try {
        await requireOrgMembership(authenticatedUser.userId, notebook.org_id);
        return notebook;
      } catch {
        return null;
      }
    },
  },

  Mutation: {
    createNotebook: async (
      _: unknown,
      args: { input: { orgId: string; name: string; description?: string } },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const { input } = args;

      const supabase = createAdminClient();
      await requireOrgMembership(authenticatedUser.userId, input.orgId);

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
      const { input } = args;

      const supabase = createAdminClient();
      const { data: notebook, error: fetchError } = await supabase
        .from("notebooks")
        .select("org_id")
        .eq("id", input.id)
        .single();

      if (fetchError || !notebook) {
        throw ResourceErrors.notFound("Notebook", input.id);
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
      const { input } = args;

      const supabase = createAdminClient();
      const { data: notebook } = await supabase
        .from("notebooks")
        .select("org_id")
        .eq("id", input.notebookId)
        .single();

      if (!notebook) {
        throw ResourceErrors.notFound("Notebook", input.notebookId);
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
