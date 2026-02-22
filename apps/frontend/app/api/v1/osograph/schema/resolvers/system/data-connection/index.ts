import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { dataConnectionMutationResolvers } from "@/app/api/v1/osograph/schema/resolvers/system/data-connection/mutations";

export const dataConnectionResolvers: GraphQLResolverModule<GraphQLContext> = {
  Mutation: { ...dataConnectionMutationResolvers.Mutation },
};
