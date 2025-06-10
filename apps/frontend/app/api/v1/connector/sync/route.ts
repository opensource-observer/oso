import { NextRequest, NextResponse } from "next/server";
import { createNormalSupabaseClient } from "../../../../../lib/clients/supabase";
import {
  getTrinoAdminClient,
  TrinoClient,
} from "../../../../../lib/clients/trino";
import { setSupabaseSession } from "../../../../../lib/auth/auth";
import { getCatalogName } from "../../../../../lib/dynamic-connectors";
import { SupabaseClient } from "@supabase/supabase-js";
import { Database } from "../../../../../lib/types/supabase";
import { logger } from "../../../../../lib/logger";

const IGNORED_SCHEMAS = new Set(["information_schema", "system"]);

async function syncSchema(
  trinoClient: TrinoClient,
  supabaseClient: SupabaseClient<Database>,
  catalogName: string,
  connectorId: string,
  schema: string,
) {
  logger.log(`Syncing schema: ${schema} for catalog: ${catalogName}`);

  const tableQueryResult = await trinoClient.queryAll(
    `SHOW TABLES FROM ${catalogName}.${schema}`,
  );

  if (tableQueryResult.error) {
    logger.error(
      `Error querying tables for schema ${schema}:`,
      tableQueryResult.error,
    );
    throw tableQueryResult.error;
  }

  const tableNames = tableQueryResult.data.flatMap((queryResult) => {
    return (
      queryResult.data?.map((row) => `${schema}.${row[0]}` as string) ?? []
    );
  });

  const columnsByTable = (
    await Promise.all(
      tableNames.map(async (table) => {
        const { data, error } = await trinoClient.queryAll(
          `SHOW COLUMNS FROM ${catalogName}.${table}`,
        );
        if (error) {
          logger.error(`Error querying columns for table ${table}:`, error);
          return { table, columns: [] };
        }
        return {
          table,
          columns: data.flatMap(
            (row) =>
              row.data?.map((col) => ({
                name: col[0] as string,
                type: col[1] as string,
              })) ?? [],
          ),
        };
      }),
    )
  ).filter((r) => r.columns.length > 0);

  const result = await Promise.all(
    columnsByTable.map(async ({ table, columns }) => {
      // Check if table context already exists
      const { data: existingTable } = await supabaseClient
        .from("dynamic_table_contexts")
        .select("id")
        .eq("connector_id", connectorId)
        .eq("table_name", table)
        .single();

      let tableId: string;
      logger.info(`Processing table: ${table}`);
      if (existingTable) {
        logger.info(`found table: ${existingTable}`);
        tableId = existingTable.id;
      } else {
        // Insert new table context
        const { data: newTable, error: tableError } = await supabaseClient
          .from("dynamic_table_contexts")
          .insert({
            connector_id: connectorId,
            table_name: table,
            description: null, // Will be populated later with LLM-generated descriptions
          })
          .select("id")
          .single();

        if (tableError) {
          logger.error(
            `Error inserting table context for ${table}:`,
            tableError,
          );
          return false;
        }

        logger.info(`created table: ${newTable}`);

        tableId = newTable.id;
      }

      logger.log(`Found ${columns.length} columns in table ${table}`);

      // Insert or update column contexts
      if (columns.length > 0) {
        // Delete old column contexts that are not in the current columns list
        await supabaseClient
          .from("dynamic_column_contexts")
          .delete()
          .eq("table_id", tableId)
          .not("column_name", "in", `(${columns})`);

        const { error: columnError } = await supabaseClient
          .from("dynamic_column_contexts")
          .upsert(
            columns.map((column) => ({
              table_id: tableId,
              column_name: column.name,
              data_type: column.type,
            })),
          );

        if (columnError) {
          logger.error(
            `Error inserting column contexts for ${table}:`,
            columnError,
          );
          return false;
        }
      }

      return true;
    }),
  );

  logger.log(`Finished schema: ${schema}`);
  return { tables: tableNames, success: result.every((res) => res) };
}

export async function POST(request: NextRequest) {
  const supabaseClient = createNormalSupabaseClient();
  const trinoClient = getTrinoAdminClient();
  const auth = await setSupabaseSession(supabaseClient, request);
  if (auth.error) {
    return NextResponse.json(
      { error: `Authorization error: ${auth.error}` },
      { status: 401 },
    );
  }

  const id = request.nextUrl.searchParams.get("id") || "";
  if (!id) {
    return NextResponse.json(
      { error: "Invalid request body. 'id' is required." },
      { status: 400 },
    );
  }

  const { data: connector, error } = await supabaseClient
    .from("dynamic_connectors")
    .select("*")
    .eq("id", id)
    .single();

  if (error) {
    return NextResponse.json(
      { error: `Error fetching dynamic connector: ${error.message}` },
      { status: 500 },
    );
  }
  if (!connector) {
    return NextResponse.json(
      { error: `Dynamic connector ${id} not found.` },
      { status: 404 },
    );
  }

  const catalogName = getCatalogName(
    connector.connector_name,
    connector.is_public,
  );

  const { data: schemaQueryResult, error: trinoError } =
    await trinoClient.queryAll(`SHOW SCHEMAS FROM ${catalogName}`);

  if (trinoError) {
    logger.error("Error querying schemas:", trinoError);
    return NextResponse.json(
      { error: `Error querying schemas: ${trinoError.message}` },
      { status: 500 },
    );
  }

  const schemas = schemaQueryResult.flatMap((queryResult) => {
    return (
      queryResult.data
        ?.map((row: any) => row[0] as string)
        .filter((schema: string) => !IGNORED_SCHEMAS.has(schema)) ?? []
    );
  });

  logger.log(`Found ${schemas.length} schemas to sync for connector ${id}`);

  // Sync each schema
  const result = await Promise.all(
    schemas.map((schema: string) =>
      syncSchema(trinoClient, supabaseClient, catalogName, id, schema),
    ),
  );

  if (!result.every((res) => res.success)) {
    return NextResponse.json(
      { error: "Failed to sync some schemas." },
      { status: 500 },
    );
  }

  // Cleanup tables that do not exist anymore
  const { error: cleanupError } = await supabaseClient
    .from("dynamic_table_contexts")
    .delete()
    .not("table_name", "in", `(${result.flatMap((r) => r.tables)})`)
    .eq("connector_id", id);
  if (cleanupError) {
    logger.error("Error cleaning up old tables:", cleanupError);
    return NextResponse.json(
      { error: `Error cleaning up old tables: ${cleanupError.message}` },
      { status: 500 },
    );
  }

  return NextResponse.json({
    message: `Successfully synced ${schemas.length} schemas`,
    schemas: schemas,
  });
}
