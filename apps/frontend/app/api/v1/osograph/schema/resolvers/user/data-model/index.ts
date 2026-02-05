import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { dataModelQueries } from "@/app/api/v1/osograph/schema/resolvers/user/data-model/queries";

export const dataModelResolvers: GraphQLResolverModule<GraphQLContext> = {
  Query: {
    ...dataModelQueries,
  },
};
