import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import {
  UpdateStaticModelSchema,
  validateInput,
} from "@/app/api/v1/osograph/utils/validation";
import { logger } from "@/lib/logger";
import {
  ResourceErrors,
  ServerErrors,
} from "@/app/api/v1/osograph/utils/errors";
import { StaticModelUpdate } from "@/lib/types/schema-types";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import { putSignedUrl } from "@/lib/clients/cloudflare-r2";
import { getOrgResourceClient } from "@/app/api/v1/osograph/utils/access-control";
import {
  MutationCreateStaticModelUploadUrlArgs,
  MutationDeleteStaticModelArgs,
  MutationUpdateStaticModelArgs,
} from "@/lib/graphql/generated/graphql";

const FILES_BUCKET = "static-model-files";
const SIGNED_URL_EXPIRY = 900;

/**
 * Static model mutations that operate on existing static model resources.
 * These resolvers use getOrgResourceClient for fine-grained permission checks.
 */
export const staticModelMutations: GraphQLResolverModule<GraphQLContext>["Mutation"] =
  {
    updateStaticModel: async (
      _: unknown,
      { input }: MutationUpdateStaticModelArgs,
      context: GraphQLContext,
    ) => {
      const validatedInput = validateInput(UpdateStaticModelSchema, input);

      const { client } = await getOrgResourceClient(
        context,
        "static_model",
        validatedInput.staticModelId,
        "write",
      );

      const updateData: StaticModelUpdate = {};
      if (validatedInput.name !== undefined) {
        updateData.name = validatedInput.name;
      }
      if (Object.keys(updateData).length > 0) {
        updateData.updated_at = new Date().toISOString();
      }

      const { data, error } = await client
        .from("static_model")
        .update(updateData)
        .eq("id", validatedInput.staticModelId)
        .select()
        .single();

      if (error) {
        logger.error("Failed to update staticModel:", error);
        throw ServerErrors.database("Failed to update staticModel");
      }

      return {
        success: true,
        message: "StaticModel updated successfully",
        staticModel: data,
      };
    },

    createStaticModelUploadUrl: async (
      _: unknown,
      { staticModelId }: MutationCreateStaticModelUploadUrlArgs,
      context: GraphQLContext,
    ) => {
      const { client } = await getOrgResourceClient(
        context,
        "static_model",
        staticModelId,
        "write",
      );

      const { data: staticModel, error: staticModelError } = await client
        .from("static_model")
        .select("org_id, dataset_id")
        .eq("id", staticModelId)
        .single();

      if (staticModelError || !staticModel) {
        throw ResourceErrors.notFound("StaticModel", staticModelId);
      }

      const presignedUrl = await putSignedUrl(
        FILES_BUCKET,
        `${staticModel.dataset_id}/${staticModelId}`,
        SIGNED_URL_EXPIRY,
      );

      return presignedUrl;
    },

    deleteStaticModel: async (
      _: unknown,
      { id }: MutationDeleteStaticModelArgs,
      context: GraphQLContext,
    ) => {
      const { client } = await getOrgResourceClient(
        context,
        "static_model",
        id,
        "admin",
      );

      const { error } = await client
        .from("static_model")
        .update({ deleted_at: new Date().toISOString() })
        .eq("id", id);

      if (error) {
        throw ServerErrors.database(
          `Failed to delete static model: ${error.message}`,
        );
      }

      return {
        success: true,
        message: "StaticModel deleted successfully",
      };
    },
  };
