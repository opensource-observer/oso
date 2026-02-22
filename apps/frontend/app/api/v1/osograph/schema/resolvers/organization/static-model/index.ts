import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { staticModelMutations } from "@/app/api/v1/osograph/schema/resolvers/organization/static-model/mutations";

export const staticModelResolvers: GraphQLResolverModule<GraphQLContext> = {
  Mutation: { ...staticModelMutations },
};
