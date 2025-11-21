/**
 * Wrap the query rewriter in typescript.
 */
import { loadPyodideEnvironment } from "@opensource-observer/pyodide-node-toolkit";

export type RewriteOptions = {
  orgName: string;
  query: string;
  dialect?: string;
};

export interface TableResolver {
  resolveTables(tables: string[]): Promise<Record<string, string>>;
}

export class PyodideQueryRewriter {
  private tableResolver: TableResolver;
  private envTarballPath: string;
  private pyodide: Awaited<ReturnType<typeof loadPyodideEnvironment>> | null =
    null;

  constructor(envTarballPath: string, tableResolver: TableResolver) {
    this.envTarballPath = envTarballPath;
    this.tableResolver = tableResolver;
    this.pyodide = null;
  }

  async initialize() {
    this.pyodide = await loadPyodideEnvironment(this.envTarballPath);

    this.pyodide.registerJsModule("js_table_resolver", {
      resolve_tables: async (tables: string[]) => {
        return await this.tableResolver.resolveTables(tables);
      },
    });
  }

  async rewrite({
    query,
    orgName,
    dialect = "trino",
  }: RewriteOptions): Promise<string> {
    if (!this.pyodide) {
      await this.initialize();
    }
    const pyLocals = this.pyodide!.toPy({
      query: query,
      org_name: orgName,
      dialect: dialect,
    });

    const rewrittenQuery = await this.pyodide!.runPythonAsync(
      `
        from queryrewriter.defaults import default_oso_table_rewrite_js

        import js_table_resolver

        await default_oso_table_rewrite_js(
            query=query,
            org_name=org_name, 
            js_name_resolver=js_table_resolver.resolve_tables
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
