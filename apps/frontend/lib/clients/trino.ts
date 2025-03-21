import { BasicAuth, QueryError, Trino } from "trino-client";
import { TRINO_PASSWORD, TRINO_URL, TRINO_USERNAME } from "../config";

const TRINO_CLIENT = Trino.create({
  server: TRINO_URL,
  catalog: "iceberg",
  schema: "oso",
  auth: new BasicAuth(TRINO_USERNAME, TRINO_PASSWORD),
});

export function getTrinoClient() {
  return TRINO_CLIENT;
}

export class TrinoError extends Error {
  constructor(error: QueryError) {
    super(`${error.errorName}: ${error.message}`);
    this.name = "TrinoError";
  }
}
