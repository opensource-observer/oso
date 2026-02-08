/**
 * Async query tools
 *
 * This allows us to make `/api/v1/sql` and `/api/v1/async-sql` calls share
 * common code for the majority of the logic (e.g caching, authentication,
 * credit checks, queuing). The major difference is that `/api/v1/sql` returns
 * results by polling the `Run` table for results and `/api/v1/async-sql`
 * assumes the user will do the polling.
 */
import { type NextRequest, NextResponse } from "next/server";
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
import { hashObject } from "@/lib/utils-server";

import { ASYNC_QUERY_BUCKET, ORG_CACHE_BUCKET } from "@/lib/config";
import { getFromRunMetadata } from "@/lib/runs/utils";
import { validStatusCodeOr500 } from "@/lib/utils/status-codes";
import { ErrorDetailsSchema } from "@/app/api/v1/osograph/utils/validation";
import { Json } from "@/lib/types/supabase";
import { AuthOrgUser } from "@/lib/types/user";

// Next.js route control
export const revalidate = 0;

export type AsyncSqlQueryResponse = {
  runId: string;
  status: string;
};

export type AsyncSqlQueryOptions = {
  request: NextRequest;
  query: string;
  waitForCompletion?: boolean;
  metadata?: Record<string, unknown>;
};

const makeErrorResponse = (errorMsg: string, status: number) =>
  NextResponse.json({ error: errorMsg }, { status });

/**
 * Makes an async SQL query by enqueuing it for processing.
 * @param request
 * @param query
 *
 * @returns The run id of the enqueued query
 */
export async function makeAsyncSqlQuery({
  request,
  query,
  metadata = {},
}: AsyncSqlQueryOptions): Promise<NextResponse> {
  logger.info(`Starting async SQL query: ${query}`);

  const queryKey = hashObject({ query });

  const user = await getOrgUser(request);
  const tracker = trackServerEvent(user);

  if (!query) {
    logger.warn(`makeAsyncSqlQuery: Missing query`);
    return makeErrorResponse("Please provide a 'query' parameter", 400);
  }

  if (user.role === "anonymous") {
    logger.warn(`makeAsyncSqlQuery: User is anonymous`);
    return makeErrorResponse("Authentication required", 401);
  }

  // Add orgName to metadata
  if (metadata["orgName"] === undefined) {
    metadata["orgName"] = user.orgName;
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
      `makeAsyncSqlQuery: Error tracking usage for user ${user.userId}:`,
      error,
    );
  }

  // Try to get from private organization cache
  if (orgPlan?.plan_name === "ENTERPRISE") {
    try {
      if (await fileExists(ORG_CACHE_BUCKET, `${user.orgName}/${queryKey}`)) {
        logger.log(`makeAsyncSqlQuery: Private cache hit, short-circuiting`);
        const cachedUrl = await getSignedUrl(
          ORG_CACHE_BUCKET,
          `${user.orgName}/${queryKey}`,
        );

        return NextResponse.json({
          id: queryKey,
          status: "completed",
          url: cachedUrl,
        });
      }
    } catch (error) {
      logger.log(`makeAsyncSqlQuery: No private cache hit, ${error}`);
    }
  }

  try {
    const run = await createQueryRun(user, query, metadata);

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
    logger.error(`makeAsyncSqlQuery: Error queuing message: ${error}`);
    return makeErrorResponse("Failed to queue query execution", 500);
  }
}

export async function createQueryRun(
  user: AuthOrgUser,
  query: string,
  metadata: Record<string, unknown>,
) {
  const queryKey = hashObject({ query });
  const metadataJson = JSON.stringify(metadata);
  // Create run in Supabase
  const supabase = createAdminClient();
  const { data: run, error: runError } = await supabase
    .from("run")
    .insert({
      org_id: user.orgId,
      run_type: "manual",
      requested_by: user.userId,
      status: "queued",
      metadata: {
        queryHash: queryKey,
        queryMetadataJson: metadataJson,
      },
    })
    .select("id, status")
    .single();

  if (runError) {
    logger.error(`makeAsyncSqlQuery: Error creating run: ${runError.message}`);
    throw new Error("Failed to create run");
  }

  // Enqueue message
  const message: QueryRunRequest = {
    runId: new Uint8Array(Buffer.from(run.id.replace(/-/g, ""), "hex")),
    query: query,
    user: `ro-${user.orgName.trim().toLowerCase()}-${user.orgId.trim().replace(/-/g, "").toLowerCase()}`,
    metadataJson: metadataJson,
  };

  const queueService = createQueueService();
  const result = await queueService.queueMessage({
    queueName: "query_run_requests",
    message: message,
    encoder: QueryRunRequest,
  });

  if (!result.success) {
    throw new Error(result.error?.message || "Unknown queue error");
  }

  return run;
}

export type RetrieveAsyncSqlQueryResultsOptions = {
  runId: string;
  user: Awaited<ReturnType<typeof getOrgUser>>;
};

type RetrieveAsyncSqlQueryResultsResponse =
  | {
      error: string;
      statusCode: number;
    }
  | {
      id: string;
      status: "completed" | "running" | "queued";
      url?: string;
    };

function createErrorResponseFromErrorDetails(run: {
  metadata: Json | null;
  status_code: number;
}): RetrieveAsyncSqlQueryResultsResponse {
  const errorDetails = getFromRunMetadata<string>(run, "errorDetails");
  const { data, error, success } = ErrorDetailsSchema.safeParse(errorDetails);
  if (!success) {
    logger.error("Failed to parse error details from run metadata:", error);
    // FIXME: we should setup alerts to monitor these cases
    return {
      error: "Query execution failed for unknown reasons. Contact support.",
      statusCode: 500,
    };
  }
  const statusCode = validStatusCodeOr500(run.status_code);
  return {
    error: `${data.error_type}: ${data.error_name} - ${data.message}`,
    statusCode,
  };
}

export async function retrieveAsyncSqlQueryResults({
  runId,
  user,
}: RetrieveAsyncSqlQueryResultsOptions): Promise<RetrieveAsyncSqlQueryResultsResponse> {
  if (user.role === "anonymous") {
    return { error: "Authentication required", statusCode: 401 };
  }

  const supabase = createAdminClient();
  const { data: run, error } = await supabase
    .from("run")
    .select(
      "status, completed_at, logs_url, requested_by, metadata, status_code",
    ) // minimal fields
    .eq("id", runId)
    .single();

  if (error || !run) {
    return { error: "Run not found", statusCode: 404 };
  }

  if (run.requested_by !== user.userId) {
    return { error: "Unauthorized", statusCode: 403 };
  }

  if (run.status === "queued" || run.status === "running") {
    return {
      id: runId,
      status: run.status,
    };
  } else if (run.status === "failed") {
    return createErrorResponseFromErrorDetails(run);
  } else if (run.status === "canceled") {
    return {
      error: "Query execution canceled",
      statusCode: validStatusCodeOr500(run.status_code),
    };
  } else if (run.status !== "completed") {
    assertNever(run.status, `Unknown run status: ${run.status}`);
  }

  const url = await getSignedUrl(ASYNC_QUERY_BUCKET, runId);

  const queryHash = getFromRunMetadata<string>(run, "queryHash");
  const containsUdmReference =
    getFromRunMetadata<boolean>(run, "containsUdmReference") || false;

  if (queryHash && !containsUdmReference) {
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

  return {
    id: runId,
    status: run.status,
    url,
  };
}
