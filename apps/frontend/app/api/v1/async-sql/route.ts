import { type NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { getOrgUser, signTrinoJWT } from "@/lib/auth/auth";
import { trackServerEvent } from "@/lib/analytics/track";
import { logger } from "@/lib/logger";
import { EVENTS } from "@/lib/types/posthog";
import {
  CreditsService,
  InsufficientCreditsError,
  TransactionType,
} from "@/lib/services/credits";
import { createQueueService } from "@/lib/services/queue";
import { createAdminClient } from "@/lib/supabase/admin";
import { QueryRunRequest } from "@opensource-observer/osoprotobufs/query";
import { getSignedUrl } from "@/lib/clients/gcs";
import { assertNever } from "@opensource-observer/utils";
import { withPostHogTracking } from "@/lib/clients/posthog";

const ASYNC_QUERY_BUCKET = "oso-async-query";

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

  // TODO(icaro): Check cache here and avoid creating a run?

  const user = await getOrgUser(request);
  const tracker = trackServerEvent(user);

  if (!query) {
    logger.warn(`/api/async-sql: Missing query`);
    return makeErrorResponse("Please provide a 'query' parameter", 400);
  }

  if (user.role === "anonymous") {
    logger.warn(`/api/async-sql: User is anonymous`);
    return makeErrorResponse("Authentication required", 401);
  }

  // Credit check
  try {
    await CreditsService.checkAndDeductOrganizationCredits(
      user,
      user.orgId,
      TransactionType.SQL_QUERY,
      tracker,
    );
  } catch (error) {
    if (error instanceof InsufficientCreditsError) {
      return makeErrorResponse(error.message, 402);
    }
    logger.error(
      `/api/async-sql: Error tracking usage for user ${user.userId}:`,
      error,
    );
  }

  // Create run in Supabase
  const supabase = createAdminClient();
  const { data: run, error: runError } = await supabase
    .from("run")
    .insert({
      org_id: user.orgId,
      run_type: "manual",
      requested_by: user.userId,
      status: "queued",
    })
    .select("id")
    .single();

  if (runError) {
    logger.error(`/api/async-sql: Error creating run: ${runError.message}`);
    return makeErrorResponse("Failed to create run", 500);
  }

  // Sign JWT
  const jwt = await signTrinoJWT(user);

  // Enqueue message
  const message: QueryRunRequest = {
    runId: new Uint8Array(Buffer.from(run.id.replace(/-/g, ""), "hex")),
    query: query,
    jwt: jwt,
    metadataJson: JSON.stringify({}),
  };

  try {
    const queueService = createQueueService();
    const result = await queueService.queueMessage({
      queueName: "query_run_requests",
      message: message,
      encoder: QueryRunRequest,
    });

    if (!result.success) {
      throw new Error(result.error?.message || "Unknown queue error");
    }

    tracker.track(EVENTS.API_CALL, {
      type: "async-sql",
      query: query,
      apiKeyName: user.keyName,
      host: user.host,
      runId: run.id,
    });

    return NextResponse.json({ id: run.id }, { status: 202 });
  } catch (error) {
    logger.error(`/api/async-sql: Error queuing message: ${error}`);
    return makeErrorResponse("Failed to queue query execution", 500);
  }
});

export const GET = withPostHogTracking(async (request: NextRequest) => {
  const searchParams = request.nextUrl.searchParams;
  const runId = searchParams.get("id");

  if (!runId) {
    return makeErrorResponse("Missing id parameter", 400);
  }

  const user = await getOrgUser(request);
  if (user.role === "anonymous") {
    return makeErrorResponse("Authentication required", 401);
  }

  const supabase = createAdminClient();
  const { data: run, error } = await supabase
    .from("run")
    .select("status, completed_at, logs_url") // minimal fields
    .eq("id", runId)
    .single();

  if (error || !run) {
    return makeErrorResponse("Run not found", 404);
  }

  if (run.status === "queued" || run.status === "running") {
    return NextResponse.json({
      id: runId,
      status: run.status,
    });
  } else if (run.status === "failed") {
    return makeErrorResponse("Query execution failed", 500);
  } else if (run.status === "canceled") {
    return makeErrorResponse("Query execution canceled", 400);
  } else if (run.status !== "completed") {
    assertNever(run.status, `Unknown run status: ${run.status}`);
  }

  const resultUrl = await getSignedUrl(ASYNC_QUERY_BUCKET, `${runId}.csv.gz`);

  return NextResponse.json({
    id: runId,
    status: run.status,
    completedAt: run.completed_at,
    resultUrl,
  });
});
