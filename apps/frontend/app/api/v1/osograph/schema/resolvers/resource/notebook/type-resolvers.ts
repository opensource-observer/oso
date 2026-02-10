import {
  getOrganization,
  getUserProfile,
} from "@/app/api/v1/osograph/utils/auth";
import { getPreviewSignedUrl } from "@/lib/clients/cloudflare-r2";
import { logger } from "@/lib/logger";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { getOrgResourceClient } from "@/app/api/v1/osograph/utils/access-control";
import { NotebooksRow } from "@/lib/types/schema-types";

const PREVIEWS_BUCKET = "notebook-previews";
const SIGNED_URL_EXPIRY = 900;

/**
 * Type resolvers for Notebook.
 * These field resolvers don't require auth checks as they operate on
 * already-fetched notebook data.
 */
export const notebookTypeResolvers: GraphQLResolverModule<GraphQLContext> = {
  Notebook: {
    name: (parent: NotebooksRow) => parent.notebook_name,
    createdAt: (parent: NotebooksRow) => parent.created_at,
    updatedAt: (parent: NotebooksRow) => parent.updated_at,
    creatorId: (parent: NotebooksRow) => parent.created_by,
    orgId: (parent: NotebooksRow) => parent.org_id,

    creator: async (
      parent: NotebooksRow,
      _args: unknown,
      context: GraphQLContext,
    ) => {
      const { client } = await getOrgResourceClient(
        context,
        "notebook",
        parent.id,
      );
      return getUserProfile(parent.created_by, client);
    },

    organization: async (
      parent: NotebooksRow,
      _args: unknown,
      context: GraphQLContext,
    ) => {
      const { client } = await getOrgResourceClient(
        context,
        "notebook",
        parent.id,
      );
      return getOrganization(parent.org_id, client);
    },

    preview: async (parent: NotebooksRow) => {
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
