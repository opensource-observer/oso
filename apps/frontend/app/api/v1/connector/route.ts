import { NextRequest, NextResponse } from "next/server";
import { getTrinoAdminClient } from "@/lib/clients/trino";
import { createServerClient } from "@/lib/supabase/server";
import { ALLOWED_CONNECTORS } from "@/lib/types/dynamic-connector";
import { dynamicConnectorsInsertSchema } from "@/lib/types/schema";
import type { DynamicConnectorsInsert } from "@/lib/types/schema-types";
import { ensure } from "@opensource-observer/utils";
import { setSupabaseSession } from "@/lib/auth/auth";
import { Tables } from "@/lib/types/supabase";
import { getCatalogName } from "@/lib/dynamic-connectors";

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
    ...(dynamicConnector.config ? Object.entries(dynamicConnector.config) : []),
    ...Object.entries(credentials),
  ];

  const query = `CREATE CATALOG ${getCatalogName(dynamicConnector.connector_name, dynamicConnector.is_public)} USING ${dynamicConnector.connector_type} ${
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

  const query = `DROP CATALOG ${getCatalogName(deletedConnector.data.connector_name, deletedConnector.data.is_public)}`;
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
