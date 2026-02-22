import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { stepTypeResolvers } from "@/app/api/v1/osograph/schema/resolvers/organization/step/type-resolvers";

export const stepResolvers: GraphQLResolverModule<GraphQLContext> = {
  ...stepTypeResolvers,
};
