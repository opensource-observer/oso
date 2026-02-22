import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { materializationTypeResolvers } from "@/app/api/v1/osograph/schema/resolvers/organization/materialization/type-resolvers";

export const materializationResolvers: GraphQLResolverModule<GraphQLContext> = {
  ...materializationTypeResolvers,
};
