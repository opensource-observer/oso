import {
  BasicAuth,
  QueryError,
  QueryResult,
  Iterator,
  Trino,
} from "trino-client";
import { TRINO_ADMIN_PASSWORD, TRINO_ADMIN_USER, TRINO_URL } from "../config";

export function getTrinoClient(jwt: string) {
  return new TrinoClient(
    Trino.create({
      server: TRINO_URL,
      catalog: "iceberg",
      schema: "oso",
      extraHeaders: {
        Authorization: `Bearer ${jwt}`,
        "X-Trino-User": "", // For some reason this lib adds this header by default and this is the only way to remove it
      },
    }),
  );
}

export function getTrinoAdminClient() {
  return new TrinoClient(
    Trino.create({
      server: TRINO_URL,
      catalog: "iceberg",
      schema: "oso",
      auth: new BasicAuth(TRINO_ADMIN_USER, TRINO_ADMIN_PASSWORD),
    }),
  );
}

class TrinoClient {
  private client: Trino;

  constructor(client: Trino) {
    this.client = client;
  }

  async query(query: string): Promise<[QueryResult, Iterator<QueryResult>]> {
    const rows = await this.client.query(query);
    // We check the first row of the returned data to see if there was an error in the query
    const firstRow = await rows.next();
    if (firstRow.value.error) {
      throw new TrinoError(firstRow.value.error);
    }
    return [firstRow.value, rows];
  }
}

export class TrinoError extends Error {
  constructor(error: QueryError) {
    super(`${error.errorName}: ${error.message}`);
    this.name = "TrinoError";
  }
}
