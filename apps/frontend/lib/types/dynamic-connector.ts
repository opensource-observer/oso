export const ALLOWED_CONNECTORS = ["postgresql", "gsheets"];

export type ConnectorType = (typeof ALLOWED_CONNECTORS)[number];

export const DYNAMIC_CONNECTOR_NAME_REGEX = /^[a-z][a-z0-9_-]*$/;
