import { type NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { getOrgUser } from "@/lib/auth/auth";
import { trackServerEvent } from "@/lib/analytics/track";
import { logger } from "@/lib/logger";
import { EVENTS } from "@/lib/types/posthog";
import {
  CreditsService,
  InsufficientCreditsError,
  OrganizationPlan,
  TransactionType,
} from "@/lib/services/credits";
import { createQueueService } from "@/lib/services/queue";
import { createAdminClient } from "@/lib/supabase/admin";
import { QueryRunRequest } from "@opensource-observer/osoprotobufs/query";
import { copyFile, fileExists, getSignedUrl } from "@/lib/clients/gcs";
import { assertNever } from "@opensource-observer/utils";
import { withPostHogTracking } from "@/lib/clients/posthog";
import { hashObject } from "@/lib/utils-server";

const PUBLIC_CACHE_BUCKET = "oso-public-sql-cache";
const ORG_CACHE_BUCKET = "oso-org-sql-cache";
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

  // First try to serve from a public cache (anon is okay)
  const queryKey = hashObject(reqBody.data);

  try {
    if (await fileExists(PUBLIC_CACHE_BUCKET, queryKey)) {
      logger.log(`/api/async-sql: Public cache hit, short-circuiting`);
      const cachedUrl = await getSignedUrl(PUBLIC_CACHE_BUCKET, queryKey);
      return NextResponse.json({
        id: queryKey,
        status: "completed",
        url: cachedUrl,
      });
    }
  } catch (error) {
    logger.log(`/api/sql: No public cache hit, ${error}`);
  }

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
  let orgPlan: OrganizationPlan | null = null;
  try {
    orgPlan = await CreditsService.checkAndDeductOrganizationCredits(
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

  // Try to get from private organization cache
  if (orgPlan?.plan_name === "ENTERPRISE") {
    try {
      if (await fileExists(ORG_CACHE_BUCKET, `${user.orgName}/${queryKey}`)) {
        logger.log(`/api/async-sql: Private cache hit, short-circuiting`);
        const cachedUrl = await getSignedUrl(
          ORG_CACHE_BUCKET,
          `${user.orgName}/${queryKey}`,
        );

        await copyFile(
          {
            bucketName: ORG_CACHE_BUCKET,
            fileName: `${user.orgName}/${queryKey}`,
          },
          {
            bucketName: PUBLIC_CACHE_BUCKET,
            fileName: queryKey,
          },
        );

        return NextResponse.json({
          id: queryKey,
          status: "completed",
          url: cachedUrl,
        });
      }
    } catch (error) {
      logger.log(`/api/async-sql: No private cache hit, ${error}`);
    }
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
      metadata: { queryHash: queryKey },
    })
    .select("id, status")
    .single();

  if (runError) {
    logger.error(`/api/async-sql: Error creating run: ${runError.message}`);
    return makeErrorResponse("Failed to create run", 500);
  }

  // Enqueue message
  const message: QueryRunRequest = {
    runId: new Uint8Array(Buffer.from(run.id.replace(/-/g, ""), "hex")),
    query: query,
    user: `jwt-${user.orgName}`, // Prefix with 'jwt-' for backwards compatibility for now
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

    return NextResponse.json(
      { id: run.id, status: run.status },
      { status: 202 },
    );
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
    .select("status, completed_at, logs_url, requested_by, metadata") // minimal fields
    .eq("id", runId)
    .single();

  if (error || !run) {
    return makeErrorResponse("Run not found", 404);
  }

  if (run.requested_by !== user.userId) {
    return makeErrorResponse("Unauthorized", 403);
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

  const url = await getSignedUrl(ASYNC_QUERY_BUCKET, runId);
  const queryHash =
    typeof run.metadata === "object" && !Array.isArray(run.metadata)
      ? run.metadata?.["queryHash"]
      : undefined;

  if (queryHash) {
    const orgPlan = await CreditsService.getOrganizationPlan(user.orgId);
    if (orgPlan?.plan_name === "ENTERPRISE") {
      await copyFile(
        {
          bucketName: ASYNC_QUERY_BUCKET,
          fileName: runId,
        },
        {
          bucketName: ORG_CACHE_BUCKET,
          fileName: `${user.orgName}/${queryHash}`,
        },
      );
    }
  }

  return NextResponse.json({
    id: runId,
    status: run.status,
    url,
  });
});
