import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { datasetMutations } from "@/app/api/v1/osograph/schema/resolvers/organization/dataset/mutations";

export const datasetResolvers: GraphQLResolverModule<GraphQLContext> = {
  Mutation: { ...datasetMutations },
};
