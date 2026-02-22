import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { notebookMutations } from "@/app/api/v1/osograph/schema/resolvers/organization/notebook/mutations";

export const notebookResolvers: GraphQLResolverModule<GraphQLContext> = {
  Mutation: { ...notebookMutations },
};
