import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { organizationQueries } from "@/app/api/v1/osograph/schema/resolvers/user/organization/queries";

export const organizationResolvers: GraphQLResolverModule<GraphQLContext> = {
  Query: {
    ...organizationQueries,
  },
};
