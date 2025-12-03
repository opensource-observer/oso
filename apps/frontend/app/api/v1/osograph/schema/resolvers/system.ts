import { createAdminClient } from "@/lib/supabase/admin";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { AuthenticationErrors } from "@/app/api/v1/osograph/utils/errors";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import { Table } from "@/lib/types/table";
import { LegacyInferredTableResolver } from "@/lib/query/resolvers/legacy-table-resolver";
import { DBTableResolver } from "@/lib/query/resolvers/db-table-resolver";
import { TableResolutionMap } from "@/lib/query/resolver";
import { MetadataInferredTableResolver } from "@/lib/query/resolvers/metadata-table-resolver";
import {
  ResolveTablesSchema,
  validateInput,
} from "@/app/api/v1/osograph/utils/validation";

export const systemResolvers: GraphQLResolverModule<GraphQLContext> = {
  Query: {
    system: async (_: unknown, _args: unknown, context: GraphQLContext) => {
      if (!context.systemCredentials) {
        throw AuthenticationErrors.notAuthorized();
      }
      return {};
    },
  },
  System: {
    resolveTables: async (
      _: unknown,
      input: { references: string[]; orgName: string; datasetName?: string },
      context: GraphQLContext,
    ) => {
      if (!context.systemCredentials) {
        throw AuthenticationErrors.notAuthorized();
      }

      const { references, orgName, datasetName } = validateInput(
        ResolveTablesSchema,
        input,
      );

      const supabase = createAdminClient();

      const tableResolvers = [
        new LegacyInferredTableResolver(),
        ...(orgName ? [new MetadataInferredTableResolver()] : []),
        new DBTableResolver(supabase, [
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
        ]),
      ];

      let tableResolutionMap: TableResolutionMap = {};
      for (const ref of references) {
        tableResolutionMap[ref] = Table.fromString(ref);
      }

      for (const resolver of tableResolvers) {
        tableResolutionMap = await resolver.resolveTables(tableResolutionMap, {
          orgName,
          datasetName,
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
