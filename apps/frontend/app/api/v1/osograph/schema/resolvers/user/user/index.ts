import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { userTypeResolvers } from "@/app/api/v1/osograph/schema/resolvers/user/user/type-resolvers";

export const userUserResolvers: GraphQLResolverModule<GraphQLContext> = {
  ...userTypeResolvers,
};
