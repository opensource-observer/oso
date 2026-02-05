import { logger } from "@/lib/logger";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { ServerErrors } from "@/app/api/v1/osograph/utils/errors";
import {
  CreateDataModelSchema,
  validateInput,
} from "@/app/api/v1/osograph/utils/validation";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import { getOrgScopedClient } from "@/app/api/v1/osograph/utils/access-control";
import { MutationCreateDataModelArgs } from "@/lib/graphql/generated/graphql";

/**
 * Data model mutations that operate at organization scope.
 * These resolvers use getOrgScopedClient because they don't have a resourceId yet.
 */
export const dataModelMutations: GraphQLResolverModule<GraphQLContext>["Mutation"] =
  {
    createDataModel: async (
      _: unknown,
      { input }: MutationCreateDataModelArgs,
      context: GraphQLContext,
    ) => {
      const validatedInput = validateInput(CreateDataModelSchema, input);

      const { client } = await getOrgScopedClient(
        context,
        validatedInput.orgId,
      );

      const { data, error } = await client
        .from("model")
        .insert({
          org_id: validatedInput.orgId,
          dataset_id: validatedInput.datasetId,
          name: validatedInput.name,
          is_enabled: validatedInput.isEnabled,
        })
        .select()
        .single();

      if (error) {
        logger.error("Failed to create dataModel:", error);
        throw ServerErrors.database("Failed to create dataModel");
      }

      return {
        success: true,
        message: "DataModel created successfully",
        dataModel: data,
      };
    },
  };
