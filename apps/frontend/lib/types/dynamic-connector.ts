export const ALLOWED_CONNECTORS = ["postgresql", "gsheets"] as const;

export type ConnectorType = (typeof ALLOWED_CONNECTORS)[number];

export const DYNAMIC_CONNECTOR_NAME_REGEX = /^[a-z][a-z0-9_-]*$/;

export const DEFAULT_OSO_TABLE_ID = "$oso$";
