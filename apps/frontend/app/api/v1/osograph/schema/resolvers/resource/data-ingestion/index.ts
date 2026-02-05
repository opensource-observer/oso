import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { dataIngestionTypeResolvers } from "@/app/api/v1/osograph/schema/resolvers/resource/data-ingestion/type-resolvers";

/**
 * Combined data ingestion resolvers for resource-level operations.
 * Data ingestion only has type resolvers (no queries/mutations at resource level).
 */
export const dataIngestionResolvers: GraphQLResolverModule<GraphQLContext> = {
  ...dataIngestionTypeResolvers,
};
