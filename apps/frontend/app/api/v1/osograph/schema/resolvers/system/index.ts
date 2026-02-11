import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import { systemQueries } from "@/app/api/v1/osograph/schema/resolvers/system/system";
import { runMutationResolvers } from "@/app/api/v1/osograph/schema/resolvers/system/run-mutations";
import { stepMutationResolvers } from "@/app/api/v1/osograph/schema/resolvers/system/step-mutations";
import { materializationMutationResolvers } from "@/app/api/v1/osograph/schema/resolvers/system/materialization-mutations";
import { notebookPublishingResolvers } from "@/app/api/v1/osograph/schema/resolvers/system/notebook-mutations";
import { dataConnectionMutationResolvers } from "@/app/api/v1/osograph/schema/resolvers/system/data-connection-mutations";
import { systemTypeResolvers } from "@/app/api/v1/osograph/schema/resolvers/system/type-resolvers";

/**
 * Merged system resolvers with proper access control.
 * All resolvers use getSystemClient(context) for authentication.
 */
export const systemResolvers: GraphQLResolverModule<GraphQLContext> = {
  Query: {
    ...systemQueries,
  },
  Mutation: {
    ...runMutationResolvers.Mutation,
    ...stepMutationResolvers.Mutation,
    ...materializationMutationResolvers.Mutation,
    ...notebookPublishingResolvers.Mutation,
    ...dataConnectionMutationResolvers.Mutation,
  },
  System: {
    ...systemTypeResolvers.System,
  },
};
