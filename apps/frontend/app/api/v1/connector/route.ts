import { NextRequest, NextResponse } from "next/server";
import { getTrinoAdminClient } from "../../../../lib/clients/trino";
import { createNormalSupabaseClient } from "../../../../lib/clients/supabase";
import { ALLOWED_CONNECTORS } from "../../../../lib/types/dynamic-connector";
import { publicDynamicConnectorsInsertSchemaSchema } from "../../../../lib/types/schema";
import { z } from "zod";
import { ensure } from "@opensource-observer/utils";
import { setSupabaseSession } from "../../../../lib/auth/auth";
import { Tables } from "../../../../lib/types/supabase";

export const revalidate = 0;
export const maxDuration = 300;

function validateDynamicConnectorParams(
  params: z.infer<typeof publicDynamicConnectorsInsertSchemaSchema>,
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
      .startsWith(org.org_name.trim().toLowerCase())
  ) {
    return NextResponse.json(
      {
        error: `Invalid connector name: ${connector_name}. Connector name must start with the organization name: ${org.org_name}`,
      },
      { status: 400 },
    );
  }
}

function getCatalogName(connectorName: string, _?: boolean | null) {
  return `${connectorName.trim().toLocaleLowerCase()}`;
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
  const body = await request.json();
  const dynamicConnector = publicDynamicConnectorsInsertSchemaSchema.parse(
    body.data,
  );
  const credentials = ensure(body.credentials, "credentials are required");

  const { data: org, error } = await supabaseClient
    .from("organizations")
    .select()
    .eq("id", dynamicConnector.org_id)
    .single();
  if (error || !org) {
    return NextResponse.json(
      { error: `Error fetching organization: ${error.message}` },
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
    ...(dynamicConnector.config ? Object.entries(dynamicConnector.config) : []),
    ...Object.entries(credentials),
  ];

  try {
    const query = `CREATE CATALOG ${getCatalogName(dynamicConnector.connector_name, dynamicConnector.is_public)} USING ${dynamicConnector.connector_type} ${
      additionalData.length > 0
        ? `WITH (${additionalData
            .map(([key, value]) => `"${key}" = '${value}'`)
            .join(",\n")})`
        : ""
    }`;
    await trinoClient.query(query);
  } catch (e) {
    // Best effort try to cleanup the connector from supabase
    await supabaseClient
      .from("dynamic_connectors")
      .delete()
      .eq("id", insertedConnector.data.id);

    return NextResponse.json(
      {
        error: `Error creating catalog: ${e}`,
      },
      { status: 500 },
    );
  }

  return NextResponse.json(insertedConnector.data);
}

export async function DELETE(request: NextRequest) {
  const supabaseClient = createNormalSupabaseClient();
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
    .delete()
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

  try {
    const query = `DROP CATALOG ${getCatalogName(deletedConnector.data.connector_name, deletedConnector.data.is_public)}`;
    await trinoClient.query(query);
  } catch (e) {
    // Best effort reverting operation
    await supabaseClient
      .from("dynamic_connectors")
      .insert(deletedConnector.data);

    return NextResponse.json(
      {
        error: `Error creating catalog: ${e}`,
      },
      { status: 500 },
    );
  }

  return NextResponse.json(deletedConnector.data);
}
