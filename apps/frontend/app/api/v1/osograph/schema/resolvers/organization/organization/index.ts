import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { organizationResolvers as userOrganizationResolvers } from "@/app/api/v1/osograph/schema/resolvers/user/organization/index";
import { organizationMemberMutations } from "@/app/api/v1/osograph/schema/resolvers/organization/organization/mutations";
import { organizationTypeResolvers } from "@/app/api/v1/osograph/schema/resolvers/organization/organization/type-resolvers";

/**
 * Organization queries and member management mutations.
 * Uses getAuthenticatedClient for queries (defense in depth with helper filtering).
 * Uses getOrgScopedClient for mutations requiring org membership.
 */
export const organizationOrganizationResolvers: GraphQLResolverModule<GraphQLContext> =
  {
    Query: {
      ...userOrganizationResolvers.Query,
    },
    Mutation: {
      ...organizationMemberMutations,
    },
    ...organizationTypeResolvers,
  };
