import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { dataModelMutations } from "@/app/api/v1/osograph/schema/resolvers/resource/data-model/mutations";
import { dataModelTypeResolvers } from "@/app/api/v1/osograph/schema/resolvers/resource/data-model/type-resolvers";

/**
 * Combined data model resolvers for resource-level operations.
 * Uses getOrgResourceClient for fine-grained permission checks.
 */
export const dataModelResolvers: GraphQLResolverModule<GraphQLContext> = {
  Mutation: {
    ...dataModelMutations,
  },
  ...dataModelTypeResolvers,
};
