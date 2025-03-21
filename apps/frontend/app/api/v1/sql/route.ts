import { NextResponse, type NextRequest } from "next/server";

import { getTrinoClient, TrinoError } from "../../../../lib/clients/trino";
import type { QueryResult, Iterator } from "trino-client";
//import { logger } from "../../../lib/logger";

// Next.js route control
//export const runtime = "edge"; // 'nodejs' (default) | 'edge'
//export const dynamic = "force-dynamic";
export const revalidate = 0;

// HTTP headers
const QUERY_PARAM = "query";

const makeErrorResponse = (errorMsg: string, status: number) =>
  NextResponse.json({ error: errorMsg }, { status });

async function doQuery(
  rawQuery: string,
): Promise<[QueryResult, Iterator<QueryResult>]> {
  const query = decodeURIComponent(rawQuery);
  console.log(`Running query: ${query}`);
  const client = getTrinoClient();
  const rows = await client.query(query);
  // We check the first row of the returned data to see if there was an error in the query
  const firstRow = await rows.next();
  if (firstRow.value.error) {
    throw new TrinoError(firstRow.value.error);
  }
  return [firstRow.value, rows];
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
  const query = body?.[QUERY_PARAM];
  // TODO: add authentication
  //const auth = request.headers.get("authorization");

  // If no query provided, short-circuit
  if (!query) {
    console.log(`/api/sql: Missing query`);
    return makeErrorResponse("Please provide a 'query' parameter", 400);
  }
  try {
    const [firstRow, rows] = await doQuery(query);
    const textEncoder = new TextEncoder();
    const readableStream = new ReadableStream({
      async start(controller) {
        try {
          controller.enqueue(
            textEncoder.encode(
              JSON.stringify({
                columns: firstRow.columns?.map((col) => col.name),
                data: firstRow.data,
              }),
            ),
          );
          for await (const chunk of rows) {
            if (chunk.data) {
              controller.enqueue(
                textEncoder.encode(JSON.stringify({ data: chunk.data })),
              );
            }
          }
          controller.close();
        } catch (error) {
          controller.error(error);
        }
      },
    });

    return new NextResponse(readableStream);
  } catch (e) {
    if (e instanceof TrinoError) {
      return makeErrorResponse(e.message, 400);
    }
    console.log(e);
    return makeErrorResponse("Unknown error", 500);
  }
}
