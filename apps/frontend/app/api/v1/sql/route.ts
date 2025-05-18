import { NextResponse, type NextRequest } from "next/server";
import { getTrinoClient, TrinoError } from "../../../../lib/clients/trino";
import type { QueryResult, Iterator, Trino } from "trino-client";
import { spawn } from "@opensource-observer/utils";
import { withPostHog } from "../../../../lib/clients/posthog";
import { getTableNamesFromSql } from "../../../../lib/parsing";
import { getUser } from "../../../../lib/auth/auth";
import * as jsonwebtoken from "jsonwebtoken";
import { AuthUser } from "../../../../lib/types/user";
//import { logger } from "../../../lib/logger";

// Next.js route control
//export const runtime = "edge"; // 'nodejs' (default) | 'edge'
//export const dynamic = "force-dynamic";
export const revalidate = 0;
export const maxDuration = 300;

const QUERY = "query";
const FORMAT = "format";

const makeErrorResponse = (errorMsg: string, status: number) =>
  NextResponse.json({ error: errorMsg }, { status });

async function doQuery(
  client: Trino,
  query: string,
): Promise<[QueryResult, Iterator<QueryResult>]> {
  console.log(`Running query: ${query}`);
  const rows = await client.query(query);
  // We check the first row of the returned data to see if there was an error in the query
  const firstRow = await rows.next();
  if (firstRow.value.error) {
    throw new TrinoError(firstRow.value.error);
  }
  return [firstRow.value, rows];
}

function signJWT(user: AuthUser) {
  const secret = process.env.TRINO_JWT_SECRET;
  if (!secret) {
    throw new Error("JWT Secret not found: unable to authenticate");
  }
  // TODO: make subject use organization name
  return jsonwebtoken.sign(
    {
      userId: user.userId,
    },
    secret,
    {
      algorithm: "HS256",
      subject: `jwt-${user.email}`,
      audience: "consumer-trino",
      issuer: "opensource-observer",
    },
  );
}

/**
 * Run arbitrary SQL queries against Consumer Trino
 * Note: Please make sure that the server is configured with a
 *  read-only user for access
 * @param request
 * @returns
 */
export async function POST(request: NextRequest) {
  const body = await request.json();
  const query = body?.[QUERY];
  const format = body?.[FORMAT] ?? "json";
  const user = await getUser(request);

  // If no query provided, short-circuit
  if (!query) {
    console.log(`/api/sql: Missing query`);
    return makeErrorResponse("Please provide a 'query' parameter", 400);
    // If user is not authenticated, short-circuit
  } else if (user.role === "anonymous") {
    console.log(`/api/sql: User is anonymous`);
    return makeErrorResponse("User is anonymous", 401);
  }

  const jwt = signJWT(user);

  try {
    spawn(
      withPostHog(async (posthog) => {
        posthog.capture({
          distinctId: user.userId,
          event: "api_call",
          properties: {
            type: "sql",
            models: getTableNamesFromSql(query),
            query: query,
            apiKeyName: user.keyName,
            host: user.host,
          },
        });
      }),
    );
    const client = getTrinoClient(jwt);
    const [firstRow, rows] = await doQuery(client, query);
    const readableStream = mapToReadableStream(firstRow, rows, format);
    return new NextResponse(readableStream, {
      headers: {
        "Content-Type": "application/x-ndjson",
      },
    });
  } catch (e) {
    if (e instanceof TrinoError) {
      return makeErrorResponse(e.message, 400);
    }
    console.log(e);
    return makeErrorResponse("Unknown error", 500);
  }
}

function mapToReadableStream(
  firstRow: QueryResult,
  rows: Iterator<QueryResult>,
  format: "json" | "minimal",
) {
  const textEncoder = new TextEncoder();
  const columns = firstRow.columns?.map((col) => col.name) ?? [];
  const mapToFormat = (data: QueryResult["data"], isFirst: boolean = false) => {
    if (!data) {
      data = [];
    }
    if (format === "minimal") {
      if (isFirst) {
        return {
          columns: columns,
          data,
        };
      }
      return { data };
    }
    return data.map((value) => {
      const obj: Record<string, any> = {};
      for (let i = 0; i < columns.length; i++) {
        obj[columns[i]] = value[i];
      }
      return obj;
    });
  };

  return new ReadableStream({
    async start(controller) {
      try {
        controller.enqueue(
          textEncoder.encode(
            JSON.stringify(mapToFormat(firstRow.data, true)) + "\n",
          ),
        );
        for await (const chunk of rows) {
          if (chunk.data) {
            controller.enqueue(
              textEncoder.encode(
                JSON.stringify(mapToFormat(chunk.data)) + "\n",
              ),
            );
          }
        }
        controller.close();
      } catch (error) {
        controller.error(error);
      }
    },
  });
}
