import { logger } from "@/lib/logger";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { ServerErrors } from "@/app/api/v1/osograph/utils/errors";
import {
  CreateStaticModelSchema,
  validateInput,
} from "@/app/api/v1/osograph/utils/validation";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import { getOrgScopedClient } from "@/app/api/v1/osograph/utils/access-control";
import { MutationCreateStaticModelArgs } from "@/lib/graphql/generated/graphql";

/**
 * Static model mutations that operate at organization scope.
 * These resolvers use getOrgScopedClient because they don't have a resourceId yet.
 */
export const staticModelMutations: GraphQLResolverModule<GraphQLContext>["Mutation"] =
  {
    createStaticModel: async (
      _: unknown,
      { input }: MutationCreateStaticModelArgs,
      context: GraphQLContext,
    ) => {
      const validatedInput = validateInput(CreateStaticModelSchema, input);

      const { client } = await getOrgScopedClient(
        context,
        validatedInput.orgId,
      );

      const { data, error } = await client
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
  };
