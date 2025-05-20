import { NextResponse, type NextRequest } from "next/server";
import { getTrinoClient, TrinoError } from "../../../../lib/clients/trino";
import type { QueryResult, Iterator, Trino } from "trino-client";
import { getUser } from "../../../../lib/auth/auth";
import {
  CreditsService,
  TransactionType,
} from "../../../../lib/services/credits";
import { getTableNamesFromSql } from "../../../../lib/parsing";
import { trackServerEvent } from "../../../../lib/analytics/track";
import { logger } from "../../../../lib/logger";
import * as jsonwebtoken from "jsonwebtoken";
import { AuthUser } from "../../../../lib/types/user";

// Next.js route control
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
  logger.log(`Running query: ${query}`);
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
    logger.log(`/api/sql: Missing query`);
    return makeErrorResponse("Please provide a 'query' parameter", 400);
  }

  if (user.role === "anonymous") {
    logger.log(`/api/sql: User is anonymous`);
    return makeErrorResponse("Authentication required", 401);
  }

  const creditsDeducted = await CreditsService.checkAndDeductCredits(
    user,
    TransactionType.SQL_QUERY,
    "/api/v1/sql",
    { query },
  );

  if (!creditsDeducted) {
    logger.log(`/api/sql: Insufficient credits for user ${user.userId}`);
    return makeErrorResponse("Insufficient credits", 402);
  }

  const jwt = signJWT(user);

  try {
    await trackServerEvent(user, "api_call", {
      type: "sql",
      models: getTableNamesFromSql(query),
      query: query,
      apiKeyName: user.keyName,
      host: user.host,
    });

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
    logger.log(e);
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
