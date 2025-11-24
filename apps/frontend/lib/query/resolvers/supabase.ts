import { SupabaseAdminClient } from "@/lib/supabase/admin";
import { Table } from "@/lib/types/table";
import { TableResolver, TableResolutionMap } from "@/lib/query/resolver";


export type LegacyTableMappingRule = (table: Table) => Table | null;


export class SupabaseTableResolver implements TableResolver {
  private supabaseClient: SupabaseAdminClient;
  private legacyRules: LegacyTableMappingRule[];

  constructor(supabaseClient: SupabaseAdminClient, legacyRules: LegacyTableMappingRule[]) {
    this.supabaseClient = supabaseClient;
    this.legacyRules = legacyRules;
  }

  async resolveTables(tables: TableResolutionMap, metadata: Record<string, unknown>): Promise<TableResolutionMap> {
    // We expect that tables given to the supabase table resolver are fully qualified

    // If there's a legacy rule that applies use it immediately as the response
    // for the table
    const resolvedTables: TableResolutionMap = {};
    const unresolvedTables: TableResolutionMap = {};
    for (const [unresolvedName, tableObj] of Object.entries(tables)) {
      let resolvedTable: Table | null = null;
      for (const rule of this.legacyRules) {
        const result = rule(tableObj);
        if (result) {
          resolvedTable = result;
          break;
        }
      }
      if (resolvedTable) {
        resolvedTables[unresolvedName] = resolvedTable;
      } else {
        unresolvedTables[unresolvedName] = tableObj;
      }
    }

    // For any tables that are still unresolved, we will query the database.
    if (Object.keys(unresolvedTables).length === 0) {
      return resolvedTables;
    }
    // Query the table_directory for the unresolved tables
    // We should assert that all unresolved tables are fully qualified
    const fqnTables = Object.values(unresolvedTables).filter((table) => table.isFQN());
    if (fqnTables.length !== Object.keys(unresolvedTables).length) {
      throw new Error("All unresolved tables must be fully qualified names");
    }
    
    const { data, error } = await this.supabaseClient
      .from("table_directory")
      
  }
}