import { BasicAuth, QueryResult, Iterator, Trino } from "trino-client";
import { TRINO_ADMIN_PASSWORD, TRINO_ADMIN_USER, TRINO_URL } from "../config";

// Result type for error handling
export type TrinoResult<T> =
  | {
      data: T;
      error: null;
    }
  | {
      data: null;
      error: TrinoError;
    };

export type TrinoQueryResult = {
  firstRow: QueryResult;
  iterator: Iterator<QueryResult>;
};

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

export class TrinoClient {
  private client: Trino;

  constructor(client: Trino) {
    this.client = client;
  }

  async query(query: string): Promise<TrinoResult<TrinoQueryResult>> {
    try {
      const rows = await this.client.query(query);
      // We check the first row of the returned data to see if there was an error in the query
      const firstRow = await rows.next();

      if (firstRow.value.error) {
        return {
          data: null,
          error: new TrinoError(firstRow.value.error),
        };
      }
      return {
        data: {
          firstRow: firstRow.value,
          iterator: rows,
        },
        error: null,
      };
    } catch (error) {
      return {
        data: null,
        error: new TrinoError({
          errorName: "CLIENT_ERROR",
          message:
            error instanceof Error ? error.message : "Unknown error occurred",
        }),
      };
    }
  }

  async queryAll(query: string): Promise<TrinoResult<QueryResult[]>> {
    const queryResult = await this.query(query);
    if (queryResult.error) {
      return {
        data: null,
        error: queryResult.error,
      };
    }

    try {
      const { firstRow, iterator } = queryResult.data;
      const results: QueryResult[] = [firstRow];

      for await (const row of iterator) {
        if (row.error) {
          return {
            data: null,
            error: new TrinoError(row.error),
          };
        }
        results.push(row);
      }

      return {
        data: results,
        error: null,
      };
    } catch (error) {
      return {
        data: null,
        error: new TrinoError({
          errorName: "CLIENT_ERROR",
          message:
            error instanceof Error ? error.message : "Unknown error occurred",
        }),
      };
    }
  }
}

export class TrinoError extends Error {
  constructor(error: { errorName: string; message: string }) {
    super(`${error.errorName}: ${error.message}`);
    this.name = "TrinoError";
  }
}
