import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { notebookMutations } from "@/app/api/v1/osograph/schema/resolvers/resource/notebook/mutations";
import { notebookQueries } from "@/app/api/v1/osograph/schema/resolvers/resource/notebook/queries";
import { notebookTypeResolvers } from "@/app/api/v1/osograph/schema/resolvers/resource/notebook/type-resolvers";

/**
 * Combined notebook resolvers for resource-level operations.
 * Uses getOrgResourceClient for fine-grained permission checks.
 */
export const notebookResolvers: GraphQLResolverModule<GraphQLContext> = {
  Query: {
    ...notebookQueries,
  },
  Mutation: {
    ...notebookMutations,
  },
  ...notebookTypeResolvers,
};
