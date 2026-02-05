import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { notebookQueries } from "@/app/api/v1/osograph/schema/resolvers/user/notebook/queries";

export const notebookResolvers: GraphQLResolverModule<GraphQLContext> = {
  Query: {
    ...notebookQueries,
  },
};
