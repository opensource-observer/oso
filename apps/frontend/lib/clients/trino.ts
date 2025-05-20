import { QueryError, Trino } from "trino-client";
import { TRINO_URL } from "../config";

export function getTrinoClient(jwt: string) {
  return Trino.create({
    server: TRINO_URL,
    catalog: "iceberg",
    schema: "oso",
    extraHeaders: {
      Authorization: `Bearer ${jwt}`,
      "X-Trino-User": "", // For some reason this lib adds this header by default and this is the only way to remove it
    },
  });
}

export class TrinoError extends Error {
  constructor(error: QueryError) {
    super(`${error.errorName}: ${error.message}`);
    this.name = "TrinoError";
  }
}
