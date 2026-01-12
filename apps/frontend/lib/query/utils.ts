import { getTableNamesFromSql } from "@/lib/parsing";
import { Table } from "@/lib/types/table";
import {
  resolveTablesWithResolvers,
  TableResolver,
} from "@/lib/query/resolver";
import { LegacyTableMappingRule } from "@/lib/query/resolvers/db-table-resolver";
import { defaultTableMappingRules } from "@/lib/query/defaults";
import { queryMetadataSchema } from "@/lib/types/query-metadata";
import { MetadataInferredTableResolver } from "@/lib/query/resolvers/metadata-table-resolver";
import { LegacyInferredTableResolver } from "@/lib/query/resolvers/legacy-table-resolver";

export type QueryContainsUDMsReferenceOptions = {
  query: string;
  rules: LegacyTableMappingRule[];
  resolvers: TableResolver[];
  metadata: Record<string, unknown>;
};

/**
 * Given a query string, determines if it contains references to UDMs (User
 * Defined Model).
 *
 * @param query string The SQL query string to analyze.
 * @param metadata Record<string, any> The metadata object for a query. Used to
 * infer the context.
 */
export async function queryContainsUDMsReference({
  query,
  rules,
  resolvers,
  metadata,
}: QueryContainsUDMsReferenceOptions): Promise<boolean> {
  const tables = getTableNamesFromSql(query);

  // Early exit if no tables found
  if (tables.length === 0) {
    return false;
  }

  // Resolve the tables using the provided resolver
  const tableResolutionMap = tables.reduce(
    (acc, tableStr) => {
      acc[tableStr] = Table.fromString(tableStr);
      return acc;
    },
    {} as Record<string, Table>,
  );

  const resolvedTables = await resolveTablesWithResolvers({
    tables: tableResolutionMap,
    metadata,
    resolvers,
  });

  for (const [_tableKey, table] of Object.entries(resolvedTables)) {
    // If the table matches any of the legacy mapping rules, it's not a UDM reference.
    if (rules.some((rule) => rule(table) !== null)) {
      continue;
    }
    return true;
  }
  return false;
}

export type QueryContainsUDMsReferenceWithDefaultsOptions = {
  query: string;
  metadata: Record<string, unknown>;
  rules?: LegacyTableMappingRule[];
};

export async function queryContainsUDMsReferenceWithDefaults({
  query,
  metadata,
  rules = defaultTableMappingRules(),
}: QueryContainsUDMsReferenceWithDefaultsOptions): Promise<boolean> {
  const parsedMetadata = queryMetadataSchema.parse(metadata);
  const resolvers = [new MetadataInferredTableResolver()];
  // If we don't have sufficient metadata to infer tables we need to use the
  // legacy resolver rules if we're dealing with ad-hoc queries.
  if (!parsedMetadata.datasetName) {
    // Only add the legacy resolver for ad-hoc queries (this is the original
    // behavior). However, if the query is not ad-hoc, resolution will fail if
    // there is no datasetName in metadata.
    if (parsedMetadata.sourceType === "ad-hoc") {
      resolvers.unshift(new LegacyInferredTableResolver());
    }
  }
  return await queryContainsUDMsReference({
    query,
    rules,
    resolvers,
    metadata,
  });
}
