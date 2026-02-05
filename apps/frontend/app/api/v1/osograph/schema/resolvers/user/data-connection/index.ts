import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { dataConnectionQueries } from "@/app/api/v1/osograph/schema/resolvers/user/data-connection/queries";

export const dataConnectionResolvers: GraphQLResolverModule<GraphQLContext> = {
  Query: {
    ...dataConnectionQueries,
  },
};
