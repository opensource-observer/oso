import { v4 as uuidv4 } from "uuid";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { ServerErrors } from "@/app/api/v1/osograph/utils/errors";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import {
  CreateNotebookSchema,
  validateInput,
} from "@/app/api/v1/osograph/utils/validation";
import { getOrgScopedClient } from "@/app/api/v1/osograph/utils/access-control";
import { MutationCreateNotebookArgs } from "@/lib/graphql/generated/graphql";

/**
 * Notebook mutations that operate at organization scope.
 * These resolvers use getOrgScopedClient because they don't have a resourceId yet.
 */
export const notebookMutations: GraphQLResolverModule<GraphQLContext>["Mutation"] =
  {
    createNotebook: async (
      _: unknown,
      args: MutationCreateNotebookArgs,
      context: GraphQLContext,
    ) => {
      const input = validateInput(CreateNotebookSchema, args.input);

      const { client, userId } = await getOrgScopedClient(context, input.orgId);

      const notebookId = uuidv4();
      const { data: notebook, error } = await client
        .from("notebooks")
        .insert({
          id: notebookId,
          org_id: input.orgId,
          notebook_name: input.name,
          description: input.description,
          created_by: userId,
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
  };
