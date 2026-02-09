import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { runsQueries } from "@/app/api/v1/osograph/schema/resolvers/user/runs/queries";

export const runsResolvers: GraphQLResolverModule<GraphQLContext> = {
  Query: {
    ...runsQueries,
  },
};
