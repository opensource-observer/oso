import { ValidationErrors } from "@/app/api/v1/osograph/utils/errors";
import { TrinoClient } from "@/lib/clients/trino";
import {
  ALLOWED_CONNECTORS,
  ConnectorType,
} from "@/lib/types/dynamic-connector";
import { DynamicConnectorsRow } from "@/lib/types/schema-types";

const REQUIRED_CONFIG_FIELDS: Record<ConnectorType, string[]> = {
  postgresql: ["connection-url", "connection-user"],
  gsheets: ["metadata-sheet-id"],
  bigquery: ["project-id"],
};

const REQUIRED_CREDENTIALS_FIELDS: Record<ConnectorType, string[]> = {
  postgresql: ["connection-password"],
  gsheets: ["credentials-key"],
  bigquery: ["credentials-key"],
};

// TODO(icaro): change this to use orgId
export function getCatalogName(connector: DynamicConnectorsRow) {
  return `${connector.connector_name.trim().toLocaleLowerCase()}`;
}

export function validateDynamicConnector(
  name: string,
  connectorType: ConnectorType,
  config: Record<string, unknown>,
  credentials: Record<string, unknown>,
  orgName: string,
) {
  const type = ALLOWED_CONNECTORS.find((c) => c === connectorType);
  if (!type) {
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
  const requiredConfigFields = REQUIRED_CONFIG_FIELDS[connectorType] || [];
  const missingConfigFields = requiredConfigFields.filter(
    (field) => !(field in config) || config[field] === "",
  );
  if (missingConfigFields.length > 0) {
    throw ValidationErrors.validationFailed(
      [],
      `Missing required config fields for connector type ${connectorType}: ${missingConfigFields.join(
        ", ",
      )}`,
    );
  }
  const requiredCredentialsFields =
    REQUIRED_CREDENTIALS_FIELDS[connectorType] || [];
  const missingCredentialsFields = requiredCredentialsFields.filter(
    (field) => !(field in credentials) || credentials[field] === "",
  );
  if (missingCredentialsFields.length > 0) {
    throw ValidationErrors.validationFailed(
      [],
      `Missing required credentials fields for connector type ${connectorType}: ${missingCredentialsFields.join(
        ", ",
      )}`,
    );
  }
  const allFields = {
    ...config,
    ...credentials,
  };

  const quotesRegex = /['"`]/;
  for (const [key, value] of Object.entries(allFields)) {
    if (typeof value === "string" && quotesRegex.test(value)) {
      throw ValidationErrors.validationFailed(
        [],
        `Field "${key}" contains invalid characters (quotes). Please remove any single or double quotes from the value.`,
      );
    }
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
