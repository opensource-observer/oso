import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { modelContextMutations } from "@/app/api/v1/osograph/schema/resolvers/resource/model-context/mutations";
import { modelContextTypeResolvers } from "@/app/api/v1/osograph/schema/resolvers/resource/model-context/type-resolvers";

/**
 * Combined model context resolvers for resource-level operations.
 * Uses getOrgResourceClient for fine-grained permission checks.
 */
export const modelContextResolvers: GraphQLResolverModule<GraphQLContext> = {
  Mutation: {
    ...modelContextMutations,
  },
  ...modelContextTypeResolvers,
};
