import { Table } from "@/lib/types/table";
import { TableResolver, TableResolutionMap } from "@/lib/query/resolver";

export class LegacyInferredTableResolver implements TableResolver {
  async resolveTables(
    tables: TableResolutionMap,
    _metadata: Record<string, unknown>,
  ): Promise<TableResolutionMap> {
    const resolvedTables: TableResolutionMap = {};
    for (const [originalName, tableObj] of Object.entries(tables)) {
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
    return resolvedTables;
  }
}
