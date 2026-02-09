import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { staticModelMutations } from "@/app/api/v1/osograph/schema/resolvers/resource/static-model/mutations";
import { staticModelTypeResolvers } from "@/app/api/v1/osograph/schema/resolvers/resource/static-model/type-resolvers";

/**
 * Combined static model resolvers for resource-level operations.
 * Uses getOrgResourceClient for fine-grained permission checks.
 */
export const staticModelResolvers: GraphQLResolverModule<GraphQLContext> = {
  Mutation: {
    ...staticModelMutations,
  },
  ...staticModelTypeResolvers,
};
