import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { notebookPublishingResolvers } from "@/app/api/v1/osograph/schema/resolvers/system/notebook/mutations";

export const notebookResolvers: GraphQLResolverModule<GraphQLContext> = {
  Mutation: { ...notebookPublishingResolvers.Mutation },
};
