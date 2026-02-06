import { type NextRequest, NextResponse } from "next/server";
import { getOrgUser } from "@/lib/auth/auth";
import { trackServerEvent } from "@/lib/analytics/track";
import { logger } from "@/lib/logger";
import { EVENTS } from "@/lib/types/posthog";
import { z } from "zod";
import { withPostHogTracking } from "@/lib/clients/posthog";
import { getTableNamesFromSql } from "@/lib/parsing";

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

const DEPRECATION_MESSAGE = `
This endpoint is no longer available and is being deprecated. 
We may bring it back in the future but for now suggest using the 
/api/v1/async-sql endpoint.
`.replaceAll(/\s+/g, " ");

/**
 * Run arbitrary SQL queries against Consumer Trino
 * Note: Please make sure that the server is configured with a
 *  read-only user for access
 * @param request
 * @returns
 */
export const POST = withPostHogTracking(async (request: NextRequest) => {
  const reqBody = RequestBodySchema.parse(await request.json());
  const { query } = reqBody;
  logger.log(`/api/sql: ${query}`);

  const user = await getOrgUser(request);
  const tracker = trackServerEvent(user);

  if (user.role === "anonymous") {
    logger.log(`/api/sql: User is anonymous`);
    return makeErrorResponse(DEPRECATION_MESSAGE, 410);
  }

  const tables = getTableNamesFromSql(query);

  // Attempt to track the API call, but don't fail the request if tracking fails
  try {
    tracker.track(EVENTS.API_CALL, {
      type: "sql",
      models: tables,
      query: query,
      apiKeyName: user.keyName,
      host: user.host,
    });
  } catch (error) {
    logger.error("Error tracking API call", { error });
  }

  return makeErrorResponse(DEPRECATION_MESSAGE, 410);
});
