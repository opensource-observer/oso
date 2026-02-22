import { getSystemClient } from "@/app/api/v1/osograph/utils/access-control";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import { Table } from "@/lib/types/table";
import { LegacyInferredTableResolver } from "@/lib/query/resolvers/legacy-table-resolver";
import { DBTableResolver } from "@/lib/query/resolvers/db-table-resolver";
import { TableResolutionMap } from "@/lib/query/resolver";
import {
  ResolveTablesSchema,
  validateInput,
} from "@/app/api/v1/osograph/utils/validation";
import { SystemResolveTablesArgs } from "@/lib/graphql/generated/graphql";
import { LegacyTableMappingRule } from "@/lib/query/common";
import { PermissionsResolver } from "@/lib/query/resolvers/permissions-resolver";

/**
 * Type resolvers for System.
 * These resolvers require system credentials and are used for internal operations.
 */
export const systemTypeResolvers: GraphQLResolverModule<GraphQLContext> = {
  System: {
    resolveTables: async (
      _: unknown,
      input: SystemResolveTablesArgs,
      context: GraphQLContext,
    ) => {
      const client = getSystemClient(context);

      const { references, metadata } = validateInput(
        ResolveTablesSchema,
        input,
      );

      const inferredTableResolver = new LegacyInferredTableResolver();

      const legacyMappingRules: LegacyTableMappingRule[] = [
        (table) => {
          // If the catalog is iceberg return the table as is
          if (table.catalog === "iceberg") {
            return table;
          }
          return null;
        },
        (table) => {
          // If the catalog has a double underscore in the name we assume it's a
          // legacy private connector catalog and return the table as is
          if (table.catalog.includes("__")) {
            return table;
          }
          return null;
        },
      ];

      const tableResolvers = [
        inferredTableResolver,
        new PermissionsResolver(legacyMappingRules),
        new DBTableResolver(client, legacyMappingRules),
      ];

      let tableResolutionMap: TableResolutionMap = {};
      for (const ref of references) {
        tableResolutionMap[ref] = Table.fromString(ref);
      }

      for (const resolver of tableResolvers) {
        tableResolutionMap = await resolver.resolveTables(tableResolutionMap, {
          orgName: metadata?.orgName,
          datasetName: metadata?.datasetName,
        });
      }

      const results = Object.entries(tableResolutionMap).map(
        ([ref, table]) => ({
          reference: ref,
          fqn: table.toFQN(),
        }),
      );

      return results;
    },
  },
};
