import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { materializationMutationResolvers } from "@/app/api/v1/osograph/schema/resolvers/system/materialization/mutations";

export const materializationResolvers: GraphQLResolverModule<GraphQLContext> = {
  Mutation: { ...materializationMutationResolvers.Mutation },
};
