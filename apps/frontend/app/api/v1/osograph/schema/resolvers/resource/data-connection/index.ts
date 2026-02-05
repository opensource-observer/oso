import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { dataConnectionMutations } from "@/app/api/v1/osograph/schema/resolvers/resource/data-connection/mutations";
import { dataConnectionQueries } from "@/app/api/v1/osograph/schema/resolvers/resource/data-connection/queries";
import { dataConnectionTypeResolvers } from "@/app/api/v1/osograph/schema/resolvers/resource/data-connection/type-resolvers";

/**
 * Combined data connection resolvers for resource-level operations.
 * Uses getOrgResourceClient for fine-grained permission checks.
 */
export const dataConnectionResolvers: GraphQLResolverModule<GraphQLContext> = {
  Query: {
    ...dataConnectionQueries,
  },
  Mutation: {
    ...dataConnectionMutations,
  },
  ...dataConnectionTypeResolvers,
};
