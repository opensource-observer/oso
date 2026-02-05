import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { viewerQueries } from "@/app/api/v1/osograph/schema/resolvers/user/viewer/queries";
import { viewerTypeResolvers } from "@/app/api/v1/osograph/schema/resolvers/user/viewer/type-resolvers";

export const viewerResolvers: GraphQLResolverModule<GraphQLContext> = {
  Query: {
    ...viewerQueries,
  },
  ...viewerTypeResolvers,
};
