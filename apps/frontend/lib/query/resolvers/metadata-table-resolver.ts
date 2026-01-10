/**
 * A resolver that infers table mappings based on metadata.
 */
import { Table } from "@/lib/types/table";
import { queryMetadataSchema } from "@/lib/types/query-metadata";
import { TableResolver, TableResolutionMap } from "@/lib/query/resolver";

/**
 * Uses metadata to infer and resolve table names. After this resolver, all
 * tables will be fully qualified.
 */
export class MetadataInferredTableResolver implements TableResolver {
  async resolveTables(
    tables: TableResolutionMap,
    metadata: Record<string, unknown>,
  ): Promise<TableResolutionMap> {
    // Check for the orgName in metadata to infer table mappings
    const parsedMetadata = queryMetadataSchema.parse(metadata);

    const resolvedTables: TableResolutionMap = {};
    for (const [unresolvedName, tableObj] of Object.entries(tables)) {
      if (tableObj.isFQN()) {
        resolvedTables[unresolvedName] = tableObj;
      } else {
        // Infer the catalog and dataset from metadata
        let datasetName = tableObj.dataset;
        if (tableObj.dataset === "" && tableObj.catalog === "") {
          if (!parsedMetadata.datasetName) {
            throw new Error(
              `Cannot infer table mapping for "${unresolvedName}" without datasetName in metadata.`,
            );
          }
          datasetName = parsedMetadata.datasetName;
        }
        resolvedTables[unresolvedName] = new Table(
          parsedMetadata.orgName,
          datasetName,
          tableObj.table,
        );
      }
    }
    return resolvedTables;
  }
}
