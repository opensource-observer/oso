import { getAuthenticatedClient } from "@/app/api/v1/osograph/utils/access-control";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { FilterableConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import { queryWithPagination } from "@/app/api/v1/osograph/utils/query-helpers";
import { InvitationWhereSchema } from "@/app/api/v1/osograph/utils/validation";
import { getUserOrganizationIds } from "@/app/api/v1/osograph/utils/resolver-helpers";

export const invitationQueries: GraphQLResolverModule<GraphQLContext>["Query"] =
  {
    invitations: async (
      _: unknown,
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      const { client, userId } = getAuthenticatedClient(context);
      const orgIds = await getUserOrganizationIds(userId, client);

      return queryWithPagination(args, context, {
        tableName: "invitations",
        whereSchema: InvitationWhereSchema,
        client,
        orgIds,
      });
    },
  };
