import { NextResponse, type NextRequest } from "next/server";
import { getClickhouseClient } from "../../../../lib/clients/clickhouse";
import { ClickHouseError } from "@clickhouse/client";
//import { logger } from "../../../lib/logger";

// Next.js route control
//export const runtime = "edge"; // 'nodejs' (default) | 'edge'
//export const dynamic = "force-dynamic";
export const revalidate = 0;

// HTTP headers
const QUERY_PARAM = "query";

// Helper functions for creating responses suitable for Hasura
const makeErrorResponse = (errorMsg: string, status: number) =>
  NextResponse.json({ error: errorMsg }, { status });

async function doQuery(rawQuery: string) {
  const query = decodeURIComponent(rawQuery);
  console.log(`Running query: ${query}`);
  const client = getClickhouseClient();
  const rows = await client.query({ query, format: "JSONEachRow" });
  return rows;
}

/**
 * Run arbitrary SQL queries against Clickhouse
 * Note: Please make sure that the server is configured with a
 *  read-only user for access
 * @param request
 * @returns
 */
export async function POST(request: NextRequest) {
  const body = await request.json();
  const query = body?.[QUERY_PARAM];
  // TODO: add authentication
  //const auth = request.headers.get("authorization");

  // If no query provided, short-circuit
  if (!query) {
    console.log(`/api/sql: Missing query`);
    return makeErrorResponse("Please provide a 'query' parameter", 400);
  }
  try {
    const stream = (await doQuery(query)).stream();

    const readableStream = new ReadableStream({
      start(controller) {
        stream.on("data", (chunk) => {
          console.log("sending", chunk.length);
          controller.enqueue(JSON.stringify(chunk.map((r) => r.json())));
        });
        stream.on("end", () => {
          controller.close();
        });
        stream.on("error", (error) => {
          controller.error(error);
        });
      },
    });

    return new NextResponse(readableStream);
  } catch (e) {
    if (e instanceof ClickHouseError) {
      return makeErrorResponse(e.message, 400);
    }
    return makeErrorResponse("Unknown error", 500);
  }
}
