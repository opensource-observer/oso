import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { invitationMutations } from "@/app/api/v1/osograph/schema/resolvers/organization/invitation/mutations";
import { invitationTypeResolvers } from "@/app/api/v1/osograph/schema/resolvers/organization/invitation/type-resolvers";

/**
 * Organization-scoped invitation resolvers.
 * - createInvitation: uses getOrgScopedClient (orgId from input)
 * - revokeInvitation: uses getOrgScopedClient (orgId from input)
 */
export const invitationResolvers: GraphQLResolverModule<GraphQLContext> = {
  Mutation: {
    ...invitationMutations,
  },
  ...invitationTypeResolvers,
};
