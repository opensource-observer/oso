import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { stepMutationResolvers } from "@/app/api/v1/osograph/schema/resolvers/system/step/mutations";

export const stepResolvers: GraphQLResolverModule<GraphQLContext> = {
  Mutation: { ...stepMutationResolvers.Mutation },
};
