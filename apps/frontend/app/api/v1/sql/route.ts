import { type NextRequest, NextResponse } from "next/server";
import { getTrinoClient } from "@/lib/clients/trino";
import type { Iterator, QueryResult } from "trino-client";
import { getTableNamesFromSql } from "@/lib/parsing";
import { getUser } from "@/lib/auth/auth";
import { trackServerEvent } from "@/lib/analytics/track";
import { logger } from "@/lib/logger";
import { AuthUser } from "@/lib/types/user";
import { EVENTS } from "@/lib/types/posthog";
import {
  CreditsService,
  InsufficientCreditsError,
  TransactionType,
} from "@/lib/services/credits";
import { TRINO_JWT_SECRET } from "@/lib/config";
import { SignJWT } from "jose";
import {
  AssetMaterialization,
  safeGetAssetsMaterializations,
} from "@/lib/dagster/assets";
import { z } from "zod";

// Next.js route control
export const revalidate = 0;
export const maxDuration = 300;

const RequestBodySchema = z.object({
  query: z.string(),
  format: z.enum(["json", "minimal"]).default("json"),
  includeAnalytics: z.boolean().default(false),
});

const makeErrorResponse = (errorMsg: string, status: number) =>
  NextResponse.json({ error: errorMsg }, { status });

async function signJWT(user: AuthUser) {
  const secret = TRINO_JWT_SECRET;
  if (!secret) {
    throw new Error("JWT Secret not found: unable to authenticate");
  }

  return new SignJWT({
    userId: user.userId,
  })
    .setProtectedHeader({ alg: "HS256" })
    .setSubject(`jwt-${(user.orgName ?? user.email)?.trim().toLowerCase()}`)
    .setAudience("consumer-trino")
    .setIssuer("opensource-observer")
    .setExpirationTime("1h")
    .sign(new TextEncoder().encode(secret));
}

/**
 * Run arbitrary SQL queries against Consumer Trino
 * Note: Please make sure that the server is configured with a
 *  read-only user for access
 * @param request
 * @returns
 */
export async function POST(request: NextRequest) {
  const { query, format, includeAnalytics } = RequestBodySchema.parse(
    await request.json(),
  );
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
      if (error instanceof InsufficientCreditsError) {
        return makeErrorResponse(error.message, 402);
      }
      logger.error(
        `/api/sql: Error tracking usage for user ${user.userId}:`,
        error,
      );
    }
  }

  const jwt = await signJWT(user);
  const tables = getTableNamesFromSql(query);

  try {
    tracker.track(EVENTS.API_CALL, {
      type: "sql",
      models: tables,
      query: query,
      apiKeyName: user.keyName,
      host: user.host,
    });

    const client = getTrinoClient(jwt);
    const [trinoData, assets] = await Promise.all([
      client.query(query),
      includeAnalytics
        ? safeGetAssetsMaterializations(tables)
        : Promise.resolve([]),
    ]);
    const { data, error } = trinoData;
    if (error) {
      return makeErrorResponse(error.message, 400);
    }
    const readableStream = mapToReadableStream(
      data.firstRow,
      data.iterator,
      assets,
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
  assets: AssetMaterialization[],
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
        if (assets.length > 0) {
          controller.enqueue(
            textEncoder.encode(JSON.stringify({ assetStatus: assets }) + "\n"),
          );
        }
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
