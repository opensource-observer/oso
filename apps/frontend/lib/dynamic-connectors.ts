import { DynamicConnectorsRow } from "@/lib/types/schema-types";

export function getCatalogName(connector: DynamicConnectorsRow) {
  return `${connector.connector_name.trim().toLocaleLowerCase()}`;
}
