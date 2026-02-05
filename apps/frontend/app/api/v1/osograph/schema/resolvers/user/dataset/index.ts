import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { datasetQueries } from "@/app/api/v1/osograph/schema/resolvers/user/dataset/queries";

export const datasetResolvers: GraphQLResolverModule<GraphQLContext> = {
  Query: {
    ...datasetQueries,
  },
};
