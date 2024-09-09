import { NextResponse, type NextRequest } from "next/server";
import { getClickhouseClient } from "../../../../lib/clients/clickhouse";
//import { logger } from "../../../lib/logger";

// Next.js route control
//export const runtime = "edge"; // 'nodejs' (default) | 'edge'
//export const dynamic = "force-dynamic";
export const revalidate = 0;

// HTTP headers
const QUERY_PARAM = "query";

// Helper functions for creating responses suitable for Hasura
const makeError = (errorMsg: string) => ({
  error: errorMsg,
});

async function doQuery(query: string) {
  const client = getClickhouseClient();
  const rows = await client.query({
    query: query,
  });
  const resultSet = await rows.json();
  return resultSet;
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
    return NextResponse.json(makeError("Please provide a 'query' parameter"));
  }
  const result = doQuery(query);
  return NextResponse.json(result);
}

export async function POST(request: NextRequest) {
  const body = await request.json();
  const query = body[QUERY_PARAM];
  //const auth = request.headers.get("authorization");

  // If no query provided, short-circuit
  if (!query) {
    console.log(`/api/sql: Missing query`);
    return NextResponse.json(makeError("Please provide a 'query' parameter"));
  }
  const result = doQuery(query);
  return NextResponse.json(result);
}
