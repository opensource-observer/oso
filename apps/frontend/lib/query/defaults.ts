import { SupabaseAdminClient } from "@/lib/supabase/admin";
import { LegacyTableMappingRule } from "@/lib/query/resolvers/db-table-resolver";
import { QueryMetadata } from "@/lib/types/query-metadata";

export type RewriteQueryOptions = {
  query: string;
  metadata: QueryMetadata;
  adminClient: SupabaseAdminClient;
  pyodideEnvironmentPath?: string;
};

export function defaultTableMappingRules(): LegacyTableMappingRule[] {
  return [
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
}
