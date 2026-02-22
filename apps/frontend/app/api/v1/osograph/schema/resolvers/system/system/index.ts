import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { systemQueries } from "@/app/api/v1/osograph/schema/resolvers/system/system/queries";
import { systemTypeResolvers } from "@/app/api/v1/osograph/schema/resolvers/system/system/type-resolvers";

export const systemSystemResolvers: GraphQLResolverModule<GraphQLContext> = {
  Query: { ...systemQueries },
  ...systemTypeResolvers,
};
