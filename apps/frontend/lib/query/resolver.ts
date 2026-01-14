import { Table } from "@/lib/types/table";

export type TableResolutionMap = {
  [unresolvedName: string]: Table;
};

export interface TableResolver {
  resolveTables(
    tables: TableResolutionMap,
    metadata: Record<string, unknown>,
  ): Promise<TableResolutionMap>;
}

export type ResolveTablesOptions = {
  tables: TableResolutionMap;
  metadata: Record<string, unknown>;
  resolvers: TableResolver[];
};

export async function resolveTablesWithResolvers({
  tables,
  metadata,
  resolvers,
}: ResolveTablesOptions): Promise<TableResolutionMap> {
  for (const resolver of resolvers) {
    tables = await resolver.resolveTables(tables, metadata);
  }
  return tables;
}
