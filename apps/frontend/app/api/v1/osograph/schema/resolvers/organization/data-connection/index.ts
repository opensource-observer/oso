import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { dataConnectionMutations } from "@/app/api/v1/osograph/schema/resolvers/organization/data-connection/mutations";

export const dataConnectionResolvers: GraphQLResolverModule<GraphQLContext> = {
  Mutation: { ...dataConnectionMutations },
};
