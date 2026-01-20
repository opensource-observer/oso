import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import type { FilterableConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import { getUserOrganizationsConnection } from "@/app/api/v1/osograph/utils/resolver-helpers";
import {
  validateInput,
  OrganizationWhereSchema,
} from "@/app/api/v1/osograph/utils/validation";
import { parseWhereClause } from "@/app/api/v1/osograph/utils/where-parser";

export const userResolvers: GraphQLResolverModule<GraphQLContext> = {
  User: {
    fullName: (parent: { full_name: string | null }) => parent.full_name,
    avatarUrl: (parent: { avatar_url: string | null }) => parent.avatar_url,

    organizations: async (
      parent: { id: string },
      args: FilterableConnectionArgs,
      _context: GraphQLContext,
    ) => {
      const validatedWhere = args.where
        ? validateInput(OrganizationWhereSchema, args.where)
        : undefined;

      return getUserOrganizationsConnection(
        parent.id,
        args,
        validatedWhere ? parseWhereClause(validatedWhere) : undefined,
      );
    },
  },
};
