import { type NextRequest, NextResponse } from "next/server";
import { ReadableStream as WebReadableStream } from "node:stream/web";
import { getTrinoClient } from "@/lib/clients/trino";
import type { Iterator, QueryResult } from "trino-client";
import { getTableNamesFromSql } from "@/lib/parsing";
import { getUser } from "@/lib/auth/auth";
import { trackServerEvent } from "@/lib/analytics/track";
import { logger } from "@/lib/logger";
import { AuthUser } from "@/lib/types/user";
import { EVENTS } from "@/lib/types/posthog";
import {
  PlanName,
  CreditsService,
  InsufficientCreditsError,
  OrganizationPlan,
  TransactionType,
} from "@/lib/services/credits";
import { TRINO_JWT_SECRET } from "@/lib/config";
import { SignJWT } from "jose";
import {
  AssetMaterialization,
  safeGetAssetsMaterializations,
} from "@/lib/dagster/assets";
import { z } from "zod";
import {
  getObjectByQuery,
  putObjectByQuery,
} from "@/lib/clients/cloudflare-r2";
import { withPostHogTracking } from "@/lib/clients/posthog";

// Next.js route control
export const revalidate = 0;
export const maxDuration = 300;

// Globals
const PUBLIC_SQL_BUCKET = "public-sql";
const ENTERPRISE_PLAN_NAME: PlanName = "ENTERPRISE";

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
export const POST = withPostHogTracking(async (request: NextRequest) => {
  const reqBody = RequestBodySchema.parse(await request.json());
  const { query, format, includeAnalytics } = reqBody;
  logger.log(`/api/sql: ${query}`);

  // First try to serve from a public cache (anon is okay)
  try {
    const objResponse = await getObjectByQuery(PUBLIC_SQL_BUCKET, reqBody);
    //console.log(objResponse);
    if (objResponse.Body) {
      const respStream = WebReadableStream.from(objResponse.Body);
      logger.log(`/api/sql: Public cache hit, short-circuiting`);
      return new NextResponse(respStream as ReadableStream, {
        headers: {
          "Content-Type": "application/x-ndjson",
        },
      });
    }
  } catch (error) {
    logger.log(`/api/sql: No public cache hit, ${error}`);
  }

  const user = await getUser(request);
  const tracker = trackServerEvent(user);

  // If no query provided, short-circuit
  if (!query) {
    logger.log(`/api/sql: Missing query`);
    return makeErrorResponse("Please provide a 'query' parameter", 400);
  }

  if (user.role === "anonymous") {
    logger.log(`/api/sql: User is anonymous`);
    return makeErrorResponse("Authentication required", 401);
  }

  console.log(`Org: ${user.orgName}`);
  let orgPlan: OrganizationPlan | null = null;
  try {
    orgPlan = await CreditsService.checkAndDeductOrganizationCredits(
      user,
      user.orgId,
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

  // Try to get from private organization cache
  if (orgPlan?.plan_name === ENTERPRISE_PLAN_NAME) {
    try {
      const objResponse = await getObjectByQuery(user.orgName, reqBody);
      //console.log(objResponse);
      if (objResponse.Body) {
        const respStream = WebReadableStream.from(objResponse.Body);
        logger.log(`/api/sql: Private cache hit, short-circuiting`);
        return new NextResponse(respStream as ReadableStream, {
          headers: {
            "Content-Type": "application/x-ndjson",
          },
        });
      } else {
        logger.log(`/api/sql: No private cache hit (no body)`);
      }
    } catch (error) {
      logger.log(`/api/sql: No private cache hit, ${error}`);
    }
  }

  // Trino query
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

    // Clone the response stream for caching
    const readableStream = mapToReadableStream(
      data.firstRow,
      data.iterator,
      assets,
      format,
    );
    const [responseStream, cacheStream] = readableStream.tee();

    // Auto-caching is only available for Enterprise plan users
    if (orgPlan?.plan_name === ENTERPRISE_PLAN_NAME) {
      // Puts are best-effort
      try {
        await putObjectByQuery(user.orgName, reqBody, cacheStream);
        logger.log(`/api/sql: Cached SQL query response`);
      } catch (error) {
        logger.warn(`/api/sql: Failed to cache SQL query response: ${error}`);
      }
    }

    return new NextResponse(responseStream, {
      headers: {
        "Content-Type": "application/x-ndjson",
      },
    });
  } catch (e) {
    logger.log(e);
    return makeErrorResponse("Unknown error", 500);
  }
});

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
