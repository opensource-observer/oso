import { TrinoClient } from "@/lib/clients/trino";
import { DynamicConnectorsRow } from "@/lib/types/schema-types";

// TODO(icaro): change this to use orgId
export function getCatalogName(connector: DynamicConnectorsRow) {
  return `org_${connector.org_id
    .trim()
    .replace(/-/g, "")
    .toLowerCase()}_${connector.connector_name.trim().toLocaleLowerCase()}`;
}

export async function createTrinoCatalog(
  trinoClient: TrinoClient,
  connector: DynamicConnectorsRow,
  credentials: Record<string, string>,
) {
  const additionalData = [
    ...(connector.config ? Object.entries(connector.config) : []),
    ...Object.entries(credentials),
  ];
  const query = `CREATE CATALOG ${getCatalogName(connector)} USING ${connector.connector_type} ${
    additionalData.length > 0
      ? `WITH (${additionalData
          .map(([key, value]) => `"${key}" = '${value}'`)
          .join(",\n")})`
      : ""
  }`;
  return trinoClient.queryAll(query);
}

export async function deleteTrinoCatalog(
  trinoClient: TrinoClient,
  connector: DynamicConnectorsRow,
) {
  const query = `DROP CATALOG ${getCatalogName(connector)}`;
  return trinoClient.queryAll(query);
}
