import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { staticModelQueries } from "@/app/api/v1/osograph/schema/resolvers/user/static-model/queries";

export const staticModelResolvers: GraphQLResolverModule<GraphQLContext> = {
  Query: {
    ...staticModelQueries,
  },
};
