import { v4 as uuidv4 } from "uuid";
import { logger } from "@/lib/logger";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import {
  CreateDatasetSchema,
  validateInput,
} from "@/app/api/v1/osograph/utils/validation";
import { ServerErrors } from "@/app/api/v1/osograph/utils/errors";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import { getOrgScopedClient } from "@/app/api/v1/osograph/utils/access-control";
import { MutationCreateDatasetArgs } from "@/lib/graphql/generated/graphql";

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
          is_public: validated.isPublic ?? false,
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
  };
