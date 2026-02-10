import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { datasetMutations } from "@/app/api/v1/osograph/schema/resolvers/resource/dataset/mutations";
import { datasetTypeResolvers } from "@/app/api/v1/osograph/schema/resolvers/resource/dataset/type-resolvers";

/**
 * Combined dataset resolvers for resource-level operations.
 * Uses getOrgResourceClient for fine-grained permission checks.
 */
export const datasetResolvers: GraphQLResolverModule<GraphQLContext> = {
  Mutation: {
    ...datasetMutations,
  },
  ...datasetTypeResolvers,
};
