"use server";
/**
 * Wrap the query rewriter in typescript.
 */
import { loadPyodideEnvironment } from "@opensource-observer/pyodide-node-toolkit";
import { TableResolutionMap, TableResolver } from "@/lib/query/resolver";
import { Table } from "@/lib/types/table";

export type RewriteOptions = {
  metadata: Record<string, unknown>;
  query: string;
  dialect?: string;
};

export class PyodideQueryRewriter {
  private tableResolvers: TableResolver[];
  private envTarballPath: string;
  private pyodide: Awaited<ReturnType<typeof loadPyodideEnvironment>> | null =
    null;

  constructor(envTarballPath: string, tableResolvers: TableResolver[]) {
    this.envTarballPath = envTarballPath;
    this.tableResolvers = tableResolvers;
    this.pyodide = null;
  }

  async initialize() {
    this.pyodide = await loadPyodideEnvironment(this.envTarballPath);

    this.pyodide.registerJsModule("js_table_resolver", {
      resolve_tables: async (
        tables: string[],
        metadata: Record<string, unknown>,
      ): Promise<Record<string, string>> => {
        let tableResolutionMap: TableResolutionMap = {};
        for (const tableName of tables) {
          tableResolutionMap[tableName] = Table.fromString(tableName);
        }
        for (const resolver of this.tableResolvers) {
          tableResolutionMap = await resolver.resolveTables(
            tableResolutionMap,
            metadata,
          );
        }
        const resolvedTables: Record<string, string> = {};
        for (const [originalName, tableObj] of Object.entries(
          tableResolutionMap,
        )) {
          resolvedTables[originalName] = tableObj.toFQN();
        }
        return resolvedTables;
      },
    });
  }

  async rewrite({
    query,
    metadata,
    dialect = "trino",
  }: RewriteOptions): Promise<string> {
    if (!this.pyodide) {
      await this.initialize();
    }
    const pyLocals = this.pyodide!.toPy({
      query: query,
      metadata: metadata,
      dialect: dialect,
    });

    const rewrittenQuery = await this.pyodide!.runPythonAsync(
      `
        from queryrewriter.defaults import default_oso_table_rewrite_js

        import js_table_resolver

        await default_oso_table_rewrite_js(
            query=query,
            metadata=metadata,
            js_name_resolver=js_table_resolver.resolve_tables,
            dialect=dialect,
        )
    `,
      pyLocals,
    );
    if (typeof rewrittenQuery !== "string") {
      throw new Error("Rewritten query is not a string");
    }

    return rewrittenQuery as string;
  }
}
