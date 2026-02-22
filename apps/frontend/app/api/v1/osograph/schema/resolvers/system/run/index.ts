import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { runMutationResolvers } from "@/app/api/v1/osograph/schema/resolvers/system/run/mutations";

export const runResolvers: GraphQLResolverModule<GraphQLContext> = {
  Mutation: { ...runMutationResolvers.Mutation },
};
