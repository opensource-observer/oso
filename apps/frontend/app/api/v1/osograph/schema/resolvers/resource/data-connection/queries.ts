import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import { dataConnectionResolvers } from "@/app/api/v1/osograph/schema/resolvers/user/data-connection/index";

/**
 * Data connection queries for resource-level operations.
 * Uses getAuthenticatedClient for queries filtered by user's organizations.
 */
export const dataConnectionQueries: GraphQLResolverModule<GraphQLContext>["Query"] =
  {
    ...dataConnectionResolvers.Query,
  };
