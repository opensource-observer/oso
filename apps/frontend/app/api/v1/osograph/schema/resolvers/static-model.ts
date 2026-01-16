import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import {
  ConnectionArgs,
  FilterableConnectionArgs,
} from "@/app/api/v1/osograph/utils/pagination";
import { z } from "zod";
import {
  CreateStaticModelSchema,
  MaterializationWhereSchema,
  StaticModelWhereSchema,
  UpdateStaticModelSchema,
  validateInput,
} from "@/app/api/v1/osograph/utils/validation";
import { queryWithPagination } from "@/app/api/v1/osograph/utils/query-helpers";
import { StaticModelRow, StaticModelUpdate } from "@/lib/types/schema-types";
import {
  getOrganization,
  requireAuthentication,
  requireOrgMembership,
} from "@/app/api/v1/osograph/utils/auth";
import {
  getModelRunConnection,
  getResourceById,
} from "@/app/api/v1/osograph/utils/resolver-helpers";
import { createAdminClient } from "@/lib/supabase/admin";
import { logger } from "@/lib/logger";
import {
  ResourceErrors,
  ServerErrors,
} from "@/app/api/v1/osograph/utils/errors";
import { putSignedUrl } from "@/lib/clients/cloudflare-r2";

const FILES_BUCKET = "static-model-files";
const SIGNED_URL_EXPIRY = 900;

export const staticModelResolvers = {
  Query: {
    staticModels: async (
      _: unknown,
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      return queryWithPagination(args, context, {
        tableName: "static_model",
        whereSchema: StaticModelWhereSchema,
        requireAuth: true,
        filterByUserOrgs: true,
        basePredicate: {
          is: [{ key: "deleted_at", value: null }],
        },
      });
    },
  },
  Mutation: {
    createStaticModel: async (
      _: unknown,
      {
        input,
      }: {
        input: z.infer<typeof CreateStaticModelSchema>;
      },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const validatedInput = validateInput(CreateStaticModelSchema, input);
      await requireOrgMembership(
        authenticatedUser.userId,
        validatedInput.orgId,
      );

      const supabase = createAdminClient();
      const { data, error } = await supabase
        .from("static_model")
        .insert({
          org_id: validatedInput.orgId,
          dataset_id: validatedInput.datasetId,
          name: validatedInput.name,
        })
        .select()
        .single();

      if (error) {
        logger.error("Failed to create staticModel:", error);
        throw ServerErrors.database("Failed to create staticModel");
      }

      return {
        success: true,
        message: "StaticModel created successfully",
        staticModel: data,
      };
    },
    updateStaticModel: async (
      _: unknown,
      {
        input,
      }: {
        input: z.infer<typeof UpdateStaticModelSchema>;
      },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const validatedInput = validateInput(UpdateStaticModelSchema, input);
      const supabase = createAdminClient();

      const { data: dataModel, error: dataModelError } = await supabase
        .from("static_model")
        .select("org_id")
        .eq("id", validatedInput.staticModelId)
        .single();

      if (dataModelError || !dataModel) {
        throw ResourceErrors.notFound(
          "StaticModel",
          validatedInput.staticModelId,
        );
      }

      await requireOrgMembership(authenticatedUser.userId, dataModel.org_id);

      const updateData: StaticModelUpdate = {};
      if (validatedInput.name !== undefined) {
        updateData.name = validatedInput.name;
      }
      if (Object.keys(updateData).length > 0) {
        updateData.updated_at = new Date().toISOString();
      }

      const { data, error } = await supabase
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
      { staticModelId }: { staticModelId: string },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const supabase = createAdminClient();

      const { data: staticModel, error: staticModelError } = await supabase
        .from("static_model")
        .select("org_id, dataset_id")
        .eq("id", staticModelId)
        .single();

      if (staticModelError || !staticModel) {
        throw ResourceErrors.notFound("StaticModel", staticModelId);
      }

      await requireOrgMembership(authenticatedUser.userId, staticModel.org_id);

      const presignedUrl = await putSignedUrl(
        FILES_BUCKET,
        `${staticModel.dataset_id}/${staticModelId}`,
        SIGNED_URL_EXPIRY,
      );

      return presignedUrl;
    },
    deleteStaticModel: async (
      _: unknown,
      { id }: { id: string },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const supabase = createAdminClient();

      const { data: staticModel, error: fetchError } = await supabase
        .from("static_model")
        .select("org_id")
        .eq("id", id)
        .single();

      if (fetchError || !staticModel) {
        throw ResourceErrors.notFound("StaticModel", id);
      }

      await requireOrgMembership(authenticatedUser.userId, staticModel.org_id);

      const { error } = await supabase
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
  },
  StaticModel: {
    orgId: (parent: StaticModelRow) => {
      return parent.org_id;
    },
    organization: (parent: StaticModelRow) => {
      return getOrganization(parent.org_id);
    },
    dataset: (parent: StaticModelRow) => {
      return getResourceById({
        tableName: "datasets",
        id: parent.dataset_id,
        userId: "",
        checkMembership: false,
      });
    },
    createdAt: (parent: StaticModelRow) => {
      return parent.created_at;
    },
    updatedAt: (parent: StaticModelRow) => {
      return parent.updated_at;
    },
    materializations: async (
      parent: StaticModelRow,
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      return queryWithPagination(args, context, {
        tableName: "materialization",
        whereSchema: MaterializationWhereSchema,
        requireAuth: false,
        filterByUserOrgs: false,
        parentOrgIds: parent.org_id,
        basePredicate: {
          eq: [
            { key: "table_id", value: `static_model_${parent.id}` },
            { key: "dataset_id", value: parent.dataset_id },
          ],
        },
        orderBy: {
          key: "created_at",
          ascending: false,
        },
      });
    },
    runs: async (parent: StaticModelRow, args: ConnectionArgs) => {
      return getModelRunConnection(parent.dataset_id, parent.id, args);
    },
  },
};
