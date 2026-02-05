import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import { notebookResolvers } from "@/app/api/v1/osograph/schema/resolvers/user/notebook/index";

/**
 * Notebook queries for resource-level operations.
 * Uses getAuthenticatedClient for queries filtered by user's organizations.
 */
export const notebookQueries: GraphQLResolverModule<GraphQLContext>["Query"] = {
  ...notebookResolvers.Query,
};
