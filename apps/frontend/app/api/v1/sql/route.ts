import { NextResponse, type NextRequest } from "next/server";
import { getTrinoClient } from "@/lib/clients/trino";
import type { QueryResult, Iterator } from "trino-client";
import { getTableNamesFromSql } from "@/lib/parsing";
import { getUser } from "@/lib/auth/auth";
import { trackServerEvent } from "@/lib/analytics/track";
import { logger } from "@/lib/logger";
import * as jsonwebtoken from "jsonwebtoken";
import { AuthUser } from "@/lib/types/user";
import { EVENTS } from "@/lib/types/posthog";
import { CreditsService, TransactionType } from "@/lib/services/credits";

// Next.js route control
export const revalidate = 0;
export const maxDuration = 300;

const QUERY = "query";
const FORMAT = "format";

const makeErrorResponse = (errorMsg: string, status: number) =>
  NextResponse.json({ error: errorMsg }, { status });

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
      subject: `jwt-${(user.orgName ?? user.email)?.trim().toLowerCase()}`,
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
  await using tracker = trackServerEvent(user);

  // If no query provided, short-circuit
  if (!query) {
    logger.log(`/api/sql: Missing query`);
    return makeErrorResponse("Please provide a 'query' parameter", 400);
  }

  if (user.role === "anonymous") {
    logger.log(`/api/sql: User is anonymous`);
    return makeErrorResponse("Authentication required", 401);
  }

  const orgId = user.orgId;

  if (orgId) {
    try {
      await CreditsService.checkAndDeductOrganizationCredits(
        user,
        orgId,
        TransactionType.SQL_QUERY,
        "/api/v1/sql",
        { query },
      );
    } catch (error) {
      logger.error(
        `/api/sql: Error tracking usage for user ${user.userId}:`,
        error,
      );
    }
  }

  const jwt = signJWT(user);

  try {
    tracker.track(EVENTS.API_CALL, {
      type: "sql",
      models: getTableNamesFromSql(query),
      query: query,
      apiKeyName: user.keyName,
      host: user.host,
    });

    const client = getTrinoClient(jwt);
    const { data, error } = await client.query(query);
    if (error) {
      return makeErrorResponse(error.message, 400);
    }
    const readableStream = mapToReadableStream(
      data.firstRow,
      data.iterator,
      format,
    );
    return new NextResponse(readableStream, {
      headers: {
        "Content-Type": "application/x-ndjson",
      },
    });
  } catch (e) {
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
