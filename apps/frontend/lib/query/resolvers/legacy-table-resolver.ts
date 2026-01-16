import { Table } from "@/lib/types/table";
import {
  TableResolver,
  TableResolution,
  TableResolutionMap,
} from "@/lib/query/resolver";

export class LegacyInferredTableResolver implements TableResolver {
  async resolveTables(
    tables: TableResolution,
    _metadata: Record<string, unknown>,
  ): Promise<TableResolution> {
    const resolvedTables: TableResolutionMap = {};
    for (const [originalName, tableObj] of Object.entries(tables.tables)) {
      if (tableObj.isFQN()) {
        resolvedTables[originalName] = tableObj;
      } else {
        // If there is no catalog and no dataset we assume that it's referencing
        // the iceberg catalog and oso dataset
        if (tableObj.dataset === "" && tableObj.catalog === "") {
          resolvedTables[originalName] = new Table(
            "iceberg",
            "oso",
            tableObj.table,
          );
        } else if (tableObj.dataset === "oso" && tableObj.catalog === "") {
          resolvedTables[originalName] = new Table(
            "iceberg",
            tableObj.dataset,
            tableObj.table,
          );
        } else {
          resolvedTables[originalName] = tableObj;
        }
      }
    }
    return {
      tables: resolvedTables,
      errors: [],
    };
  }
}
