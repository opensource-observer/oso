import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import { runResolvers } from "@/app/api/v1/osograph/schema/resolvers/system/run/index";
import { stepResolvers } from "@/app/api/v1/osograph/schema/resolvers/system/step/index";
import { materializationResolvers } from "@/app/api/v1/osograph/schema/resolvers/system/materialization/index";
import { notebookResolvers } from "@/app/api/v1/osograph/schema/resolvers/system/notebook/index";
import { dataConnectionResolvers } from "@/app/api/v1/osograph/schema/resolvers/system/data-connection/index";
import { systemSystemResolvers } from "@/app/api/v1/osograph/schema/resolvers/system/system/index";

/**
 * Merged system resolvers with proper access control.
 * All resolvers use getSystemClient(context) for authentication.
 */
export const systemResolvers: GraphQLResolverModule<GraphQLContext> = {
  Query: {
    ...systemSystemResolvers.Query,
  },
  Mutation: {
    ...runResolvers.Mutation,
    ...stepResolvers.Mutation,
    ...materializationResolvers.Mutation,
    ...notebookResolvers.Mutation,
    ...dataConnectionResolvers.Mutation,
  },
  System: systemSystemResolvers.System,
};
