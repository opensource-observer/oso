import { NextRequest, NextResponse } from "next/server";
import { getTrinoAdminClient } from "@/lib/clients/trino";
import { createServerClient } from "@/lib/supabase/server";
import { ALLOWED_CONNECTORS } from "@/lib/types/dynamic-connector";
import { dynamicConnectorsInsertSchema } from "@/lib/types/schema";
import type { DynamicConnectorsInsert } from "@/lib/types/schema-types";
import { ensure } from "@opensource-observer/utils";
import { getUser, setSupabaseSession } from "@/lib/auth/auth";
import { Tables } from "@/lib/types/supabase";
import { getCatalogName } from "@/lib/dynamic-connectors";
import { createAdminClient } from "@/lib/supabase/admin";

export const revalidate = 0;
export const maxDuration = 300;

function validateDynamicConnectorParams(
  params: DynamicConnectorsInsert,
  credentials: Record<string, string>,
  org: Tables<"organizations">,
) {
  const { connector_name, connector_type } = params;
  if (!ALLOWED_CONNECTORS.find((c) => c === connector_type)) {
    return NextResponse.json(
      {
        error: `Invalid connector type: ${connector_type}. Allowed types are: ${ALLOWED_CONNECTORS.join(
          ", ",
        )}`,
      },
      { status: 400 },
    );
  }
  if (
    !connector_name
      .trim()
      .toLowerCase()
      .startsWith(`${org.org_name.trim().toLowerCase()}__`)
  ) {
    return NextResponse.json(
      {
        error: `Invalid connector name: ${connector_name}. Connector name must start with the organization name: ${org.org_name}`,
      },
      { status: 400 },
    );
  }
}

export async function POST(request: NextRequest) {
  const supabaseClient = await createServerClient();
  const trinoClient = getTrinoAdminClient();
  const auth = await setSupabaseSession(supabaseClient, request);
  if (auth.error) {
    return NextResponse.json(
      { error: `Authorization error: ${auth.error}` },
      { status: 401 },
    );
  }
  const body = await request.json();
  const dynamicConnector = dynamicConnectorsInsertSchema.parse(body.data);
  const credentials = ensure(body.credentials, "credentials are required");

  const { data: org, error } = await supabaseClient
    .from("organizations")
    .select()
    .eq("id", dynamicConnector.org_id)
    .single();
  if (error || !org) {
    return NextResponse.json(
      {
        error: `Error fetching organization: ${error?.message || "Organization not found"}`,
      },
      { status: 500 },
    );
  }

  const validation = validateDynamicConnectorParams(
    dynamicConnector,
    credentials,
    org,
  );
  if (validation) {
    return validation;
  }

  const insertedConnector = await supabaseClient
    .from("dynamic_connectors")
    .insert(dynamicConnector)
    .select()
    .single();
  if (insertedConnector.error || insertedConnector.count === 0) {
    return NextResponse.json(
      {
        error: `Error inserting dynamic connector: ${insertedConnector.error?.message}`,
      },
      { status: insertedConnector.status ?? 500 },
    );
  }

  const additionalData = [
    ...(insertedConnector.data.config
      ? Object.entries(insertedConnector.data.config)
      : []),
    ...Object.entries(credentials),
  ];

  const query = `CREATE CATALOG ${getCatalogName(insertedConnector.data)} USING ${insertedConnector.data.connector_type} ${
    additionalData.length > 0
      ? `WITH (${additionalData
          .map(([key, value]) => `"${key}" = '${value}'`)
          .join(",\n")})`
      : ""
  }`;
  const { error: trinoError } = await trinoClient.queryAll(query);
  if (trinoError) {
    // Best effort try to cleanup the connector from supabase
    await supabaseClient
      .from("dynamic_connectors")
      .delete()
      .eq("id", insertedConnector.data.id);

    return NextResponse.json(
      {
        error: `Error creating catalog: ${trinoError}`,
      },
      { status: 500 },
    );
  }

  return NextResponse.json(insertedConnector.data);
}

export async function DELETE(request: NextRequest) {
  const supabaseClient = await createServerClient();
  const trinoClient = getTrinoAdminClient();
  const auth = await setSupabaseSession(supabaseClient, request);
  if (auth.error) {
    return NextResponse.json(
      { error: `Authorization error: ${auth.error}` },
      { status: 401 },
    );
  }

  const id = request.nextUrl.searchParams.get("id");
  if (!id) {
    return NextResponse.json(
      { error: "Missing id parameter" },
      { status: 400 },
    );
  }

  const deletedConnector = await supabaseClient
    .from("dynamic_connectors")
    .update({
      deleted_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    })
    .eq("id", id)
    .select()
    .single();
  if (deletedConnector.error || deletedConnector.count === 0) {
    return NextResponse.json(
      {
        error: `Error deleting connector: ${deletedConnector.error?.message}`,
      },
      { status: deletedConnector.status ?? 500 },
    );
  }

  const query = `DROP CATALOG ${getCatalogName(deletedConnector.data)}`;
  const { error } = await trinoClient.queryAll(query);

  if (error) {
    // Best effort reverting operation
    await supabaseClient
      .from("dynamic_connectors")
      .update({
        deleted_at: null,
      })
      .eq("id", id);

    return NextResponse.json(
      {
        error: `Error dropping catalog: ${error}`,
      },
      { status: 500 },
    );
  }

  return NextResponse.json(deletedConnector.data);
}

interface GetConnectorResponse {
  tables: {
    name: string;
    description: string | null;
    columns: {
      name: string;
      type: string;
      description: string | null;
    }[];
  }[];
  relationships: {
    sourceTable: string;
    sourceColumn: string;
    targetTable: string;
    targetColumn: string;
  }[];
}

export async function GET(request: NextRequest) {
  const supabaseClient = await createAdminClient();
  const user = await getUser(request);
  if (user.role === "anonymous" || user.orgId == null) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { data: connectorData, error: connectorError } = await supabaseClient
    .from("dynamic_connectors")
    .select("*, dynamic_table_contexts(*, dynamic_column_contexts(*))")
    .eq("org_id", user.orgId);

  if (connectorError) {
    return NextResponse.json(
      {
        error: `Error fetching connectors: ${connectorError?.message || "Connector not found"}`,
      },
      { status: 500 },
    );
  }

  const { data: relationshipsData, error: relationshipsError } =
    await supabaseClient
      .from("connector_relationships")
      .select("*")
      .eq("org_id", user.orgId);

  if (relationshipsError) {
    return NextResponse.json(
      {
        error: `Error fetching relationships: ${relationshipsError?.message || "Relationships not found"}`,
      },
      { status: 500 },
    );
  }

  const tablesById = Object.fromEntries(
    connectorData.flatMap((connector) =>
      connector.dynamic_table_contexts.map((table) => [
        table.id,
        {
          name: `${getCatalogName(connector)}.${table.table_name}`,
          description: table.description,
          columns: table.dynamic_column_contexts.map((column) => ({
            name: column.column_name,
            type: column.data_type,
            description: column.description,
          })),
        },
      ]),
    ),
  );
  const relationships = relationshipsData
    .map((r) => {
      const sourceTable = tablesById[r.source_table_id];
      const sourceColumn = sourceTable.columns.find(
        (c) => c.name === r.source_column_name,
      );
      if (!sourceTable || !sourceColumn) {
        // Invalid source table or column
        return undefined;
      }
      if (r.target_oso_entity) {
        const osoEntity = r.target_oso_entity.split(".");
        if (osoEntity.length !== 2) {
          // Invalid OSO entity format
          return undefined;
        }
        return {
          sourceTable: sourceTable.name,
          sourceColumn: sourceColumn.name,
          targetTable: osoEntity[0],
          targetColumn: osoEntity[1],
        };
      }
      if (!r.target_table_id || !r.target_column_name) {
        return undefined;
      }
      const targetTable = tablesById[r.target_table_id];
      const targetColumn = targetTable.columns.find(
        (c) => c.name === r.target_column_name,
      );
      if (!targetTable || !targetColumn) {
        // Invalid source table or column
        return undefined;
      }
      return {
        sourceTable: sourceTable.name,
        sourceColumn: sourceColumn.name,
        targetTable: targetTable.name,
        targetColumn: targetColumn.name,
      };
    })
    .filter((relationship) => relationship !== undefined);

  return NextResponse.json<GetConnectorResponse>({
    tables: Object.entries(tablesById).map(([_, table]) => table),
    relationships,
  });
}
