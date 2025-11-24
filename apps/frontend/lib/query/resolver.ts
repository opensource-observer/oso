import { SupabaseAdminClient } from "@/lib/supabase/admin";
import { Table } from "@/lib/types/table";

export type TableResolutionMap = {
  [unresolvedName: string]: Table;
};

export interface TableResolver {
  resolveTables(tables: TableResolutionMap, metadata: Record<string, unknown>): Promise<TableResolutionMap>;
}


