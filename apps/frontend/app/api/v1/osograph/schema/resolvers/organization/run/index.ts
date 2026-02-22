import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { runMutations } from "@/app/api/v1/osograph/schema/resolvers/organization/run/mutations";
import { runTypeResolvers } from "@/app/api/v1/osograph/schema/resolvers/organization/run/type-resolvers";

export const runResolvers: GraphQLResolverModule<GraphQLContext> = {
  Mutation: { ...runMutations },
  ...runTypeResolvers,
};
