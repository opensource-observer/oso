import { SupabaseAdminClient } from "@/lib/supabase/admin";
import { Table } from "@/lib/types/table";
import { TableResolver, TableResolutionMap } from "@/lib/query/resolver";
import { logger } from "@/lib/logger";

export type LegacyTableMappingRule = (table: Table) => Table | null;

export class DBTableResolver implements TableResolver {
  private supabaseClient: SupabaseAdminClient;
  private legacyRules: LegacyTableMappingRule[];

  constructor(
    supabaseClient: SupabaseAdminClient,
    legacyRules: LegacyTableMappingRule[],
  ) {
    this.supabaseClient = supabaseClient;
    this.legacyRules = legacyRules;
  }

  async resolveTables(
    tables: TableResolutionMap,
    _metadata: Record<string, unknown>,
  ): Promise<TableResolutionMap> {
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
    const fqnTables = Object.values(unresolvedTables).filter((table) =>
      table.isFQN(),
    );
    if (fqnTables.length !== Object.keys(unresolvedTables).length) {
      throw new Error("All unresolved tables must be fully qualified names");
    }

    const { data, error } = await this.supabaseClient
      .from("table_lookup")
      .select("*")
      .in(
        "logical_fqn",
        fqnTables.map((table) => table.toFQN()),
      );
    if (error) {
      throw error;
    }
    if (!data) {
      throw new Error("No data returned from table_lookup query");
    }

    // Map the results back to the unresolved tables
    const tableFQNToTableMap: Record<string, Table> = {};
    for (const row of data) {
      // Assert logical_fqn is present
      if (!row.logical_fqn) {
        throw new Error(
          `Missing logical_fqn for table_lookup row id ${row.org_id}.${row.dataset_id}.${row.table_id}`,
        );
      }

      if (!row.warehouse_fqn) {
        // If there's no warehouse_fqn it means the table is not _yet_
        // materialized. It's up to the client to raise errors if it's missing
        // any required tables even after resolution.
        logger.info(
          `Table ${row.logical_fqn} is not yet materialized. Skipping resolution.`,
        );
        continue;
      }

      // Parse the warehouse_fqn into a Table object
      const table = Table.fromString(row.warehouse_fqn!);
      tableFQNToTableMap[row.logical_fqn] = table;
    }
    for (const [unresolvedName, tableObj] of Object.entries(unresolvedTables)) {
      const fqn = tableObj.toFQN();
      const resolvedTable = tableFQNToTableMap[fqn];
      if (resolvedTable) {
        resolvedTables[unresolvedName] = resolvedTable;
      } else {
        logger.error(
          `Could not resolve table ${fqn} from table_lookup, leaving unresolved.`,
        );
      }
    }

    return resolvedTables;
  }
}
