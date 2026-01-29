import { ValidationErrors } from "@/app/api/v1/osograph/utils/errors";
import { TrinoClient } from "@/lib/clients/trino";
import { ALLOWED_CONNECTORS } from "@/lib/types/dynamic-connector";
import { DynamicConnectorsRow } from "@/lib/types/schema-types";

// TODO(icaro): change this to use orgId
export function getCatalogName(connector: DynamicConnectorsRow) {
  return `${connector.connector_name.trim().toLocaleLowerCase()}`;
}

export function validateDynamicConnector(
  name: string,
  connectorType: string,
  orgName: string,
) {
  if (!ALLOWED_CONNECTORS.find((c) => c === connectorType)) {
    throw ValidationErrors.validationFailed(
      [],
      `Invalid connector type: ${connectorType}. Allowed types are: ${ALLOWED_CONNECTORS.join(
        ", ",
      )}`,
    );
  }
  if (
    !name.trim().toLowerCase().startsWith(`${orgName.trim().toLowerCase()}__`)
  ) {
    throw ValidationErrors.validationFailed(
      [],
      `Invalid connector name: ${name}. Connector name must start with the organization name: ${orgName}`,
    );
  }
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
