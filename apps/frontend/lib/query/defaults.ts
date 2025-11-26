import { SupabaseAdminClient } from "@/lib/supabase/admin";
import { DBTableResolver } from "@/lib/query/resolvers/db-table-resolver";
import { LegacyInferredTableResolver } from "@/lib/query/resolvers/legacy-table-resolver";
import { MetadataInferredTableResolver } from "@/lib/query/resolvers/metadata-table-resolver";
import { PyodideQueryRewriter } from "@/lib/query/rewrite";

export type RewriteQueryOptions = {
  query: string;
  orgName: string;
  adminClient: SupabaseAdminClient;
  pyodideEnvironmentPath?: string;
};

/**
 * The default query rewriting function that leverages the pyodide query
 * rewriter.
 */
export async function rewriteQuery(
  options: RewriteQueryOptions,
): Promise<string> {
  const tableResolvers = [
    new LegacyInferredTableResolver(),
    new MetadataInferredTableResolver(),
    new DBTableResolver(options.adminClient, [
      (table) => {
        // If the catalog is iceberg return the table as is
        if (table.catalog === "iceberg") {
          return table;
        }
        return null;
      },
      (table) => {
        // If the catalog has a double underscore in the name we assume it's a
        // legacy private connector catalog and return the table as is
        if (table.catalog.includes("__")) {
          return table;
        }
        return null;
      },
    ]),
  ];
  const pyodideEnvironmentPath =
    options.pyodideEnvironmentPath || process.env.PYODIDE_QUERY_WRITER_PATH;
  if (!pyodideEnvironmentPath) {
    throw new Error(
      "Pyodide environment path must be provided either via options or PYODIDE_QUERY_WRITER_PATH env var",
    );
  }

  const rewriter = new PyodideQueryRewriter(
    pyodideEnvironmentPath,
    tableResolvers,
  );
  return rewriter.rewrite({
    query: options.query,
    metadata: { orgName: options.orgName },
  });
}
