import { type NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { getOrgUser } from "@/lib/auth/auth";
import { logger } from "@/lib/logger";
import { withPostHogTracking } from "@/lib/clients/posthog";
import {
  makeAsyncSqlQuery,
  retrieveAsyncSqlQueryResults,
} from "@/lib/query/async";

// Next.js route control
export const revalidate = 0;

const RequestBodySchema = z.object({
  query: z.string(),
});

const makeErrorResponse = (errorMsg: string, status: number) =>
  NextResponse.json({ error: errorMsg }, { status });

export const POST = withPostHogTracking(async (request: NextRequest) => {
  const reqBody = RequestBodySchema.safeParse(await request.json());
  if (!reqBody.success) {
    return makeErrorResponse("Invalid request body", 400);
  }
  const { query } = reqBody.data;
  logger.info(`/api/async-sql: ${query}`);

  return await makeAsyncSqlQuery({ request, query, waitForCompletion: false });
});

export const GET = withPostHogTracking(async (request: NextRequest) => {
  const searchParams = request.nextUrl.searchParams;
  const runId = searchParams.get("id");

  if (!runId) {
    return makeErrorResponse("Missing id parameter", 400);
  }

  const results = await retrieveAsyncSqlQueryResults({
    runId,
    user: await getOrgUser(request),
  });

  if ("error" in results) {
    return makeErrorResponse(results.error, results.statusCode);
  }

  return NextResponse.json(results);
});
