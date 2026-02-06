import {
  ValidationErrors,
  ServerErrors,
  DatasetErrors,
} from "@/app/api/v1/osograph/utils/errors";
import { DatasetType } from "@/lib/types/dataset";
import { createAdminClient } from "@/lib/supabase/admin";
import {
  getOrganization,
  requireOrgMembership,
} from "@/app/api/v1/osograph/utils/auth";
import {
  createQueryRun,
  retrieveAsyncSqlQueryResults,
} from "@/lib/query/async";
import { logger } from "@/lib/logger";
import type { AuthOrgUser, AuthUser } from "@/lib/types/user";
import { PreviewData } from "@/lib/graphql/generated/graphql";

export function validateTableId(tableId: string) {
  const tableIdHasValidPrefix =
    tableId.startsWith("data_model_") ||
    tableId.startsWith("data_ingestion_") ||
    tableId.startsWith("data_connection_") ||
    tableId.startsWith("static_model_");
  if (!tableIdHasValidPrefix) {
    throw ValidationErrors.invalidInput(
      "tableId",
      "tableId must start with one of the following prefixes: data_model_, data_ingestion_, data_connection_, static_model_",
    );
  }
}

export function generateTableId(datasetType: DatasetType, modelId: string) {
  switch (datasetType) {
    case "USER_MODEL":
      return `data_model_${modelId}`;
    case "STATIC_MODEL":
      return `static_model_${modelId}`;
    case "DATA_INGESTION":
      return `data_ingestion_${modelId}`;
    case "DATA_CONNECTION":
      return `data_connection_${modelId}`;
    default:
      throw ValidationErrors.invalidInput(
        "datasetType",
        `Unsupported dataset type: ${datasetType}`,
      );
  }
}

// Constants for preview data queries
const PREVIEW_QUERY_TIMEOUT_MS = 30000; // 30 seconds
const PREVIEW_POLL_INTERVAL_MS = 1000; // 1 second
const PREVIEW_ROW_LIMIT = 25;

/**
 * Check if a materialization exists for the given org, dataset, and table
 */
async function checkMaterializationExists(
  orgId: string,
  datasetId: string,
  tableId: string,
): Promise<boolean> {
  const supabase = createAdminClient();

  const { data, error } = await supabase
    .from("materialization")
    .select("id")
    .eq("org_id", orgId)
    .eq("dataset_id", datasetId)
    .eq("table_id", tableId)
    .order("created_at", { ascending: false })
    .limit(1)
    .maybeSingle();

  if (error) {
    logger.error("Error checking materialization:", error);
    return false;
  }

  return !!data;
}

/**
 * Poll a query run until it completes or times out
 */
export async function pollQueryRunUntilComplete(
  runId: string,
  user: AuthOrgUser,
  timeoutMs: number = PREVIEW_QUERY_TIMEOUT_MS,
): Promise<string> {
  const startTime = Date.now();

  while (Date.now() - startTime < timeoutMs) {
    const data = await retrieveAsyncSqlQueryResults({ runId, user });

    if ("error" in data) {
      throw ServerErrors.internal(data.error);
    }

    if (data.status === "completed") {
      if (!data.url) {
        throw ServerErrors.externalService(
          "Query completed but no URL returned",
        );
      }
      return data.url;
    }

    await new Promise((resolve) =>
      setTimeout(resolve, PREVIEW_POLL_INTERVAL_MS),
    );
  }

  throw ServerErrors.externalService(
    "Preview query timed out after 30 seconds",
  );
}

/**
 * Fetch preview results from a signed GCS URL
 */
export async function fetchPreviewResults(url: string): Promise<any[]> {
  try {
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`Failed to fetch results: ${response.statusText}`);
    }

    const text = await response.text();

    // Parse JSONL format: each line is an array
    // First line contains column names, subsequent lines contain row values
    const lines = text
      .trim()
      .split("\n")
      .filter((line) => line.trim());

    if (lines.length === 0) {
      logger.warn("Preview results are empty");
      return [];
    }

    const arrays = lines.map((line) => JSON.parse(line));

    const columnNames = arrays[0];
    const results = arrays.slice(1).map((row) => {
      const obj: Record<string, any> = {};
      columnNames.forEach((colName: string, index: number) => {
        obj[colName] = row[index];
      });
      return obj;
    });

    return results;
  } catch (error) {
    logger.error("Error fetching preview results:", error);
    throw ServerErrors.externalService("Failed to fetch preview results");
  }
}

/**
 * Execute a preview query for a materialized table
 */
export async function executePreviewQuery(
  orgId: string,
  datasetId: string,
  tableId: string,
  user: AuthUser,
  tableName: string,
): Promise<PreviewData> {
  const supabase = createAdminClient();

  const organization = await getOrganization(orgId);
  await requireOrgMembership(user.userId, organization.id);

  const materializationExists = await checkMaterializationExists(
    orgId,
    datasetId,
    tableId,
  );
  if (!materializationExists) {
    return {
      isAvailable: false,
      rows: [],
    };
  }

  // Fetch dataset name
  const { data: dataset } = await supabase
    .from("datasets")
    .select("name")
    .eq("id", datasetId)
    .single();

  if (!dataset) {
    throw DatasetErrors.notFound();
  }

  const fqn = `${organization.org_name}.${dataset.name}.${tableName}`;

  const query = `SELECT * FROM ${fqn} LIMIT ${PREVIEW_ROW_LIMIT}`;

  logger.info(`Executing preview query for table ${tableId}: ${query}`);

  const orgUser = {
    ...user,
    orgId: organization.id,
    orgName: organization.org_name,
    orgRole: "member" as const,
  };

  const run = await createQueryRun(orgUser, query, {
    previewQuery: true,
    tableId,
  });

  logger.info(`Created preview query run ${run.id} for table ${tableId}`);

  const resultsUrl = await pollQueryRunUntilComplete(run.id, orgUser);

  logger.info(`Preview query run ${run.id} completed, fetching results`);

  const results = await fetchPreviewResults(resultsUrl);

  logger.info(
    `Preview query returned ${results.length} rows for table ${tableId}`,
  );

  return {
    isAvailable: true,
    rows: results,
  };
}
