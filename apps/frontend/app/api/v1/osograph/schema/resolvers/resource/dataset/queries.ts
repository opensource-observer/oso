import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import { datasetResolvers } from "@/app/api/v1/osograph/schema/resolvers/user/dataset/index";

/**
 * Dataset queries for resource-level operations.
 * Uses getAuthenticatedClient for queries filtered by user's organizations.
 */
export const datasetQueries: GraphQLResolverModule<GraphQLContext>["Query"] = {
  ...datasetResolvers.Query,
};
