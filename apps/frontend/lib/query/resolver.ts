import { Table } from "@/lib/types/table";

export type TableResolutionMap = {
  [unresolvedName: string]: Table;
};

export type ResolutionError = {
  error: Error;
  reference: string;
};

export type TableResolution = {
  tables: TableResolutionMap;
  errors: Array<ResolutionError>;
};

export interface TableResolver {
  resolveTables(
    tables: TableResolution,
    metadata: Record<string, unknown>,
  ): Promise<TableResolution>;
}

export type ResolveTablesOptions = {
  tables: TableResolution;
  metadata: Record<string, unknown>;
  resolvers: TableResolver[];
};

export async function resolveTablesWithResolvers({
  tables,
  metadata,
  resolvers,
}: ResolveTablesOptions): Promise<TableResolution> {
  for (const resolver of resolvers) {
    tables = await resolver.resolveTables(tables, metadata);
  }
  return tables;
}
