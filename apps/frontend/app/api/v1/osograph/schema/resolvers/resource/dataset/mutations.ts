import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import {
  UpdateDatasetSchema,
  validateInput,
} from "@/app/api/v1/osograph/utils/validation";
import { ServerErrors } from "@/app/api/v1/osograph/utils/errors";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import { getOrgResourceClient } from "@/app/api/v1/osograph/utils/access-control";
import {
  MutationDeleteDatasetArgs,
  MutationUpdateDatasetArgs,
} from "@/lib/graphql/generated/graphql";

/**
 * Dataset mutations that operate on existing dataset resources.
 * These resolvers use getOrgResourceClient for fine-grained permission checks.
 */
export const datasetMutations: GraphQLResolverModule<GraphQLContext>["Mutation"] =
  {
    updateDataset: async (
      _: unknown,
      args: MutationUpdateDatasetArgs,
      context: GraphQLContext,
    ) => {
      const input = validateInput(UpdateDatasetSchema, args.input);

      const { client } = await getOrgResourceClient(
        context,
        "dataset",
        input.id,
        "write",
      );

      const { data, error } = await client
        .from("datasets")
        .update({
          name: input.name,
          display_name: input.displayName,
          description: input.description,
          is_public: input.isPublic,
        })
        .eq("id", input.id)
        .select()
        .single();

      if (error) {
        throw ServerErrors.database(
          `Failed to update dataset: ${error.message}`,
        );
      }

      return {
        dataset: data,
        message: "Dataset updated successfully",
        success: true,
      };
    },

    deleteDataset: async (
      _: unknown,
      { id }: MutationDeleteDatasetArgs,
      context: GraphQLContext,
    ) => {
      const { client } = await getOrgResourceClient(
        context,
        "dataset",
        id,
        "admin",
      );

      const { error } = await client
        .from("datasets")
        .update({ deleted_at: new Date().toISOString() })
        .eq("id", id);

      if (error) {
        throw ServerErrors.database(
          `Failed to delete dataset: ${error.message}`,
        );
      }

      return {
        success: true,
        message: "Dataset deleted successfully",
      };
    },
  };
