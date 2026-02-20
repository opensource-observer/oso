import { v4 as uuidv4 } from "uuid";
import { logger } from "@/lib/logger";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import {
  CreateDatasetSchema,
  SubscribeToDatasetSchema,
  UnsubscribeFromDatasetSchema,
  validateInput,
} from "@/app/api/v1/osograph/utils/validation";
import {
  ResourceErrors,
  ServerErrors,
} from "@/app/api/v1/osograph/utils/errors";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import {
  getOrgScopedClient,
  getResourcePublicPermission,
} from "@/app/api/v1/osograph/utils/access-control";
import type {
  MutationCreateDatasetArgs,
  MutationSubscribeToDatasetArgs,
  MutationUnsubscribeFromDatasetArgs,
} from "@/lib/graphql/generated/graphql";

/**
 * Dataset mutations that operate at organization scope.
 * These resolvers use getOrgScopedClient because they don't have a resourceId yet.
 */
export const datasetMutations: GraphQLResolverModule<GraphQLContext>["Mutation"] =
  {
    createDataset: async (
      _: unknown,
      { input }: MutationCreateDatasetArgs,
      context: GraphQLContext,
    ) => {
      const validated = validateInput(CreateDatasetSchema, input);

      const { client, userId } = await getOrgScopedClient(
        context,
        validated.orgId,
      );

      const datasetId = uuidv4();

      const { data: dataset, error } = await client
        .from("datasets")
        .insert({
          id: datasetId,
          org_id: validated.orgId,
          name: validated.name,
          display_name: validated.displayName,
          description: validated.description,
          created_by: userId,
          dataset_type: validated.type,
        })
        .select()
        .single();

      if (error) {
        logger.error("Failed to create dataset:", error);
        throw ServerErrors.database("Failed to create dataset");
      }

      return {
        dataset,
        message: "Dataset created successfully",
        success: true,
      };
    },

    subscribeToDataset: async (
      _: unknown,
      { input }: MutationSubscribeToDatasetArgs,
      context: GraphQLContext,
    ) => {
      const validated = validateInput(SubscribeToDatasetSchema, input);
      const { client, userId } = await getOrgScopedClient(
        context,
        validated.orgId,
      );

      const publicPermission = await getResourcePublicPermission(
        validated.datasetId,
        "dataset",
        client,
      );

      if (publicPermission === "none") {
        throw ResourceErrors.notFound("Dataset", validated.datasetId);
      }

      // Insert org subscription
      const { error } = await client.from("resource_permissions").insert({
        dataset_id: validated.datasetId,
        org_id: validated.orgId,
        permission_level: "read",
        granted_by: userId,
      });

      if (error?.code === "23505") {
        return { success: true, message: "Already subscribed" };
      }
      if (error) {
        logger.error("Failed to subscribe to dataset:", error);
        throw ServerErrors.database("Failed to subscribe to dataset");
      }

      return { success: true, message: "Subscribed successfully" };
    },

    unsubscribeFromDataset: async (
      _: unknown,
      { input }: MutationUnsubscribeFromDatasetArgs,
      context: GraphQLContext,
    ) => {
      const validated = validateInput(UnsubscribeFromDatasetSchema, input);
      const { client } = await getOrgScopedClient(context, validated.orgId);

      const { error } = await client
        .from("resource_permissions")
        .update({ revoked_at: new Date().toISOString() })
        .eq("dataset_id", validated.datasetId)
        .eq("org_id", validated.orgId)
        .is("user_id", null)
        .is("revoked_at", null);

      if (error) {
        logger.error("Failed to unsubscribe from dataset:", error);
        throw ServerErrors.database("Failed to unsubscribe from dataset");
      }

      return { success: true, message: "Unsubscribed successfully" };
    },
  };
