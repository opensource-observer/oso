import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { dataModelMutations } from "@/app/api/v1/osograph/schema/resolvers/organization/data-model/mutations";

export const dataModelResolvers: GraphQLResolverModule<GraphQLContext> = {
  Mutation: { ...dataModelMutations },
};
