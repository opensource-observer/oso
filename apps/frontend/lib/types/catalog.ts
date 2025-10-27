import { z } from "zod";

export const ColumnSchema = z.object({
  name: z.string(),
  type: z.string(),
  description: z.string().nullable(),
});

export const TableSchema = z.object({
  name: z.string(),
});

export const SchemaSchema = z.object({
  name: z.string(),
  tables: z.array(TableSchema),
});

export const CatalogSchema = z.object({
  name: z.string(),
  schemas: z.array(SchemaSchema),
});

export type Column = z.infer<typeof ColumnSchema>;
export type Table = z.infer<typeof TableSchema>;
export type Schema = z.infer<typeof SchemaSchema>;
export type Catalog = z.infer<typeof CatalogSchema>;
