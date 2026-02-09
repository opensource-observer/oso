import { Table } from "@/lib/types/table";

export type LegacyTableMappingRule = (table: Table) => Table | null;
