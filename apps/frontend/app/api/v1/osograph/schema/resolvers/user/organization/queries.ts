import { getAuthenticatedClient } from "@/app/api/v1/osograph/utils/access-control";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { FilterableConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import { getUserOrganizationsConnection } from "@/app/api/v1/osograph/utils/resolver-helpers";
import {
  OrganizationWhereSchema,
  validateInput,
} from "@/app/api/v1/osograph/utils/validation";
import { parseWhereClause } from "@/app/api/v1/osograph/utils/where-parser";

export const organizationQueries: GraphQLResolverModule<GraphQLContext>["Query"] =
  {
    organizations: async (
      _: unknown,
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      const { client, userId, orgIds } = await getAuthenticatedClient(context);

      const validatedWhere = args.where
        ? validateInput(OrganizationWhereSchema, args.where)
        : undefined;

      const predicate = validatedWhere
        ? parseWhereClause(validatedWhere)
        : undefined;

      return getUserOrganizationsConnection(
        userId,
        args,
        predicate,
        client,
        orgIds,
      );
    },
  };
