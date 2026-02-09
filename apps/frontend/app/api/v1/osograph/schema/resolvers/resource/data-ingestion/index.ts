import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { dataIngestionTypeResolvers } from "@/app/api/v1/osograph/schema/resolvers/resource/data-ingestion/type-resolvers";
import { dataIngestionMutations } from "@/app/api/v1/osograph/schema/resolvers/resource/data-ingestion/mutations";

/**
 * Combined data ingestion resolvers for resource-level operations.
 */
export const dataIngestionResolvers: GraphQLResolverModule<GraphQLContext> = {
  Mutation: {
    ...dataIngestionMutations,
  },
  ...dataIngestionTypeResolvers,
};
