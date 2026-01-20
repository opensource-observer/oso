import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import type { FilterableConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import { getUserOrganizationsConnection } from "@/app/api/v1/osograph/utils/resolver-helpers";
import {
  validateInput,
  OrganizationWhereSchema,
} from "@/app/api/v1/osograph/utils/validation";
import { parseWhereClause } from "@/app/api/v1/osograph/utils/where-parser";
import { UserProfilesRow } from "@/lib/types/schema-types";

export const userResolvers: GraphQLResolverModule<GraphQLContext> = {
  User: {
    fullName: (parent: UserProfilesRow) => parent.full_name,
    avatarUrl: (parent: UserProfilesRow) => parent.avatar_url,
    email: (parent: UserProfilesRow) => parent.email,
    organizations: async (
      parent: UserProfilesRow,
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
