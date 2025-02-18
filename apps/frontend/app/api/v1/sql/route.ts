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
  const rows = await client.query({ query });
  const resultSet = await rows.json();
  const data = resultSet.data;
  return data;
}

/**
 * Run arbitrary SQL queries against Clickhouse
 * Note: Please make sure that the server is configured with a
 *  read-only user for access
 * @param request
 * @returns
 */
export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const query = searchParams.get(QUERY_PARAM);
  //const auth = request.headers.get("authorization");

  // If no query provided, short-circuit
  if (!query) {
    console.log(`/api/sql: Missing query`);
    return makeErrorResponse("Please provide a 'query' parameter", 400);
  }
  try {
    const result = await doQuery(query);
    return NextResponse.json(result);
  } catch (e) {
    if (e instanceof ClickHouseError) {
      return makeErrorResponse(e.message, 400);
    }
    return makeErrorResponse("Unknown error", 500);
  }
}
