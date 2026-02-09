import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { organizationMemberMutations } from "@/app/api/v1/osograph/schema/resolvers/organization/organization/mutations";
import { organizationTypeResolvers } from "@/app/api/v1/osograph/schema/resolvers/organization/organization/type-resolvers";

/**
 * Organization member management mutations.
 * Uses getOrgScopedClient for mutations requiring org membership.
 */
export const organizationOrganizationResolvers: GraphQLResolverModule<GraphQLContext> =
  {
    Mutation: {
      ...organizationMemberMutations,
    },
    ...organizationTypeResolvers,
  };
