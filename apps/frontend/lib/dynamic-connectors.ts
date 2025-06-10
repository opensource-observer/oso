export function getCatalogName(connectorName: string, _?: boolean | null) {
  return `${connectorName.trim().toLocaleLowerCase()}`;
}
