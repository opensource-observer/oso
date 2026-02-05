import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { invitationResolvers as userInvitationResolvers } from "@/app/api/v1/osograph/schema/resolvers/user/invitation/index";
import { invitationMutations } from "@/app/api/v1/osograph/schema/resolvers/organization/invitation/mutations";
import { invitationTypeResolvers } from "@/app/api/v1/osograph/schema/resolvers/organization/invitation/type-resolvers";

/**
 * Organization-scoped invitation resolvers.
 * - invitations query: uses getAuthenticatedClient + queryWithPagination filters by orgs (defense in depth)
 * - createInvitation: uses getOrgScopedClient (orgId from input)
 * - revokeInvitation: uses getOrgScopedClient (orgId from input)
 */
export const invitationResolvers: GraphQLResolverModule<GraphQLContext> = {
  Query: {
    ...userInvitationResolvers.Query,
  },
  Mutation: {
    ...invitationMutations,
  },
  ...invitationTypeResolvers,
};
