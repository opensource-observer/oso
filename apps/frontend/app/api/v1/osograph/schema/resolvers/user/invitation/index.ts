import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { invitationMutations } from "@/app/api/v1/osograph/schema/resolvers/user/invitation/mutations";
import { invitationQueries } from "@/app/api/v1/osograph/schema/resolvers/user/invitation/queries";
import { invitationTypeResolvers } from "@/app/api/v1/osograph/schema/resolvers/user/invitation/type-resolvers";

/**
 * User-scoped invitation resolvers.
 * - acceptInvitation: uses getAuthenticatedClient (creates membership for authenticated user)
 */
export const invitationResolvers: GraphQLResolverModule<GraphQLContext> = {
  Query: {
    ...invitationQueries,
  },
  Mutation: {
    ...invitationMutations,
  },
  ...invitationTypeResolvers,
};
