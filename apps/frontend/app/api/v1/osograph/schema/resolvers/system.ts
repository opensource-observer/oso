import { createAdminClient } from "@/lib/supabase/admin";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import {
  AuthenticationErrors,
  ResourceErrors,
  ServerErrors,
  ValidationErrors,
} from "@/app/api/v1/osograph/utils/errors";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import { Table } from "@/lib/types/table";
import { LegacyInferredTableResolver } from "@/lib/query/resolvers/legacy-table-resolver";
import { DBTableResolver } from "@/lib/query/resolvers/db-table-resolver";
import { TableResolutionMap } from "@/lib/query/resolver";
import { MetadataInferredTableResolver } from "@/lib/query/resolvers/metadata-table-resolver";
import {
  CreateMaterializationSchema,
  FinishRunSchema,
  FinishStepSchema,
  UpdateRunMetadataSchema,
  ResolveTablesSchema,
  StartRunSchema,
  StartStepSchema,
  validateInput,
  UpdateMetadataSchema,
  SavePublishedNotebookHtmlSchema,
} from "@/app/api/v1/osograph/utils/validation";
import z from "zod";
import { logger } from "@/lib/logger";
import { Json } from "@/lib/types/supabase";
import { generatePublishedNotebookPath } from "@/lib/notebook/utils";
import { revalidateTag } from "next/cache";

type SystemMutationOptions<T extends z.ZodTypeAny, O> = {
  inputSchema: T;
  resolver: (input: z.infer<T>, context: GraphQLContext) => Promise<O>;
};

function systemMutation<T extends z.ZodTypeAny, O>({
  inputSchema,
  resolver,
}: SystemMutationOptions<T, O>): (
  _: any,
  args: { input: z.infer<T> },
  context: GraphQLContext,
) => Promise<O> {
  return async (
    _: any,
    args: { input: z.infer<T> },
    context: GraphQLContext,
  ) => {
    if (!context.systemCredentials) {
      throw AuthenticationErrors.notAuthorized();
    }

    const validatedInput = validateInput(inputSchema, args.input);
    return resolver(validatedInput, context);
  };
}

// Convert RunStatus enum from GraphQL to db run_status string
type RunStatus = "queued" | "running" | "completed" | "failed" | "canceled";
const RunStatusMap: Record<string, RunStatus> = {
  QUEUED: "queued",
  RUNNING: "running",
  SUCCESS: "completed",
  FAILED: "failed",
  CANCELED: "canceled",
};

type StepStatus = "running" | "success" | "failed" | "canceled";
const StepStatusMap: Record<string, StepStatus> = {
  RUNNING: "running",
  SUCCESS: "success",
  FAILED: "failed",
  CANCELED: "canceled",
};

/**
 * Update the existing metadata with the provided update. The existing metadata
 * _must_ be a valid object or an error is thrown which will result in a 500.
 *
 * The update can either replace the existing metadata or merge with it based on
 * the `merge` flag in the update argument.
 *
 * @param existing - existing metadata object
 * @param update - optional update to apply
 *
 * @returns the updated metadata object
 */
function updateMetadata(
  existing: Json,
  update?: z.infer<typeof UpdateMetadataSchema>,
): Record<string, any> {
  try {
    const parsedExisting = z.record(z.any()).parse(existing || {});
    if (!update) {
      return parsedExisting;
    }
    if (update.merge) {
      return { ...parsedExisting, ...update.value };
    } else {
      return update.value;
    }
  } catch (e) {
    throw ServerErrors.internal(
      `Existing metadata is not a valid object: ${e}`,
    );
  }
}

export const systemResolvers: GraphQLResolverModule<GraphQLContext> = {
  Mutation: {
    startRun: systemMutation({
      inputSchema: StartRunSchema,
      resolver: async (input) => {
        const supabase = createAdminClient();

        const { runId } = input;

        const { data: runData, error: runError } = await supabase
          .from("run")
          .select("*")
          .eq("id", runId)
          .single();
        if (runError || !runData) {
          throw ResourceErrors.notFound(`Run ${runId} not found`);
        }
        // Update the status of the run to "RUNNING"
        const { data: updatedRun, error: updateError } = await supabase
          .from("run")
          .update({ status: "running", started_at: new Date().toISOString() })
          .eq("id", runId)
          .select()
          .single();
        if (updateError || !updatedRun) {
          throw ServerErrors.internal(
            `Failed to update run ${runId} status to running`,
          );
        }
        return {
          message: "Marked run as running",
          success: true,
          run: updatedRun,
        };
      },
    }),
    finishRun: systemMutation({
      inputSchema: FinishRunSchema,
      resolver: async (input) => {
        const supabase = createAdminClient();

        const { status, statusCode, runId, logsUrl, metadata } = input;

        const { data: runData, error: runError } = await supabase
          .from("run")
          .select("*")
          .eq("id", runId)
          .single();
        if (runError || !runData) {
          throw ResourceErrors.notFound(`Run ${runId} not found`);
        }

        const updatedMetadata = updateMetadata(runData.metadata, metadata);

        // Update the status and logsUrl of the run based on the input
        const { data: updatedRun, error: updateError } = await supabase
          .from("run")
          .update({
            status: RunStatusMap[status] || "failed",
            status_code: statusCode,
            logs_url: logsUrl,
            completed_at: new Date().toISOString(),
            metadata: updatedMetadata,
          })
          .eq("id", runId)
          .select()
          .single();
        if (updateError || !updatedRun) {
          throw ServerErrors.internal(
            `Failed to update run ${runId} status to ${input.status}`,
          );
        }
        return {
          message: "Committed run completion",
          success: true,
          run: updatedRun,
        };
      },
    }),
    updateRunMetadata: systemMutation({
      inputSchema: UpdateRunMetadataSchema,
      resolver: async (input) => {
        const supabase = createAdminClient();

        const { runId } = input;

        const { data: runData, error: runError } = await supabase
          .from("run")
          .select("*")
          .eq("id", runId)
          .single();
        if (runError || !runData) {
          throw ResourceErrors.notFound(`Run ${runId} not found`);
        }

        const updatedMetadata = updateMetadata(
          runData.metadata,
          input.metadata,
        );

        // Update the metadata of the run
        const { data: updatedRun, error: updateError } = await supabase
          .from("run")
          .update({
            metadata: updatedMetadata,
          })
          .eq("id", runId)
          .select()
          .single();
        if (updateError || !updatedRun) {
          throw ServerErrors.internal(
            `Failed to update metadata for run ${runId}`,
          );
        }
        return {
          message: "Updated run metadata",
          success: true,
          run: updatedRun,
        };
      },
    }),
    startStep: systemMutation({
      inputSchema: StartStepSchema,
      resolver: async (input) => {
        const supabase = createAdminClient();

        const { runId, name, displayName } = input;

        // Get the run to ensure it exists
        const { data: runData, error: runError } = await supabase
          .from("run")
          .select("org_id")
          .eq("id", runId)
          .single();
        if (runError || !runData) {
          throw ResourceErrors.notFound(`Run ${runId} not found`);
        }

        // We start a new step for the given run
        const { data: stepData, error: stepError } = await supabase
          .from("step")
          .insert({
            run_id: runId,
            name,
            org_id: runData.org_id,
            display_name: displayName,
            status: "running",
            started_at: new Date().toISOString(),
          })
          .select()
          .single();
        if (stepError || !stepData) {
          throw ServerErrors.internal(
            `Failed to start step ${name} for run ${runId}`,
          );
        }
        return { message: "Started step", success: true, step: stepData };
      },
    }),
    finishStep: systemMutation({
      inputSchema: FinishStepSchema,
      resolver: async (input) => {
        const supabase = createAdminClient();

        const { stepId, logsUrl, status } = input;

        const { data: stepData, error: stepError } = await supabase
          .from("step")
          .select("*")
          .eq("id", stepId)
          .single();
        if (stepError || !stepData) {
          throw ResourceErrors.notFound(`Step ${stepId} not found`);
        }
        // Update the status and logsUrl of the step based on the input
        const { data: updatedStep, error: updateError } = await supabase
          .from("step")
          .update({
            status: StepStatusMap[status] || "failed",
            logs_url: logsUrl,
            completed_at: new Date().toISOString(),
          })
          .eq("id", stepId)
          .select()
          .single();
        if (updateError || !updatedStep) {
          throw ServerErrors.internal(
            `Failed to update step ${stepId} status to ${input.status}`,
          );
        }
        return {
          message: "Committed step completion",
          success: true,
          step: updatedStep,
        };
      },
    }),
    createMaterialization: systemMutation({
      inputSchema: CreateMaterializationSchema,
      resolver: async (input) => {
        const supabase = createAdminClient();

        const { stepId, tableId, schema, warehouseFqn } = input;

        // Assert that the tableId has one of the appropriate prefixes
        const tableIdHasValidPrefix =
          tableId.startsWith("data_model_") ||
          tableId.startsWith("data_ingestion_") ||
          tableId.startsWith("data_connection_") ||
          tableId.startsWith("static_model_");
        if (!tableIdHasValidPrefix) {
          throw ValidationErrors.invalidInput(
            "tableId",
            "tableId must start with one of the following prefixes: data_model_, data_ingestion_, data_connection_",
          );
        }

        logger.info(`Creating materialization for step ${stepId}`);

        // Get the step
        const { data: stepData, error: stepError } = await supabase
          .from("step")
          .select("*")
          .eq("id", stepId)
          .single();
        if (stepError || !stepData) {
          logger.error(`Step ${stepId} not found: ${stepError?.message}`);
          throw ResourceErrors.notFound(`Step ${stepId} not found`);
        }

        // Get the dataset id from the run associated with the step
        const { data: runData, error: runError } = await supabase
          .from("run")
          .select("id, org_id, dataset_id")
          .eq("id", stepData.run_id)
          .single();
        if (runError || !runData) {
          logger.error(
            `Run for step ${stepId} not found: ${runError?.message}`,
          );
          throw ResourceErrors.notFound(`Run for step ${stepId} not found`);
        }

        if (runData.dataset_id === null) {
          logger.error(`Dataset ID for run ${runData.id} is null`);
          throw ValidationErrors.invalidInput(
            "stepId",
            `Associated run ${runData.id} does not have a dataset_id. ` +
              "Can only create materializations for dataset runs.",
          );
        }

        // Convert schema object to supported format (remove undefined)
        const dbSafeSchema = schema.map((entry) => {
          return {
            name: entry.name,
            type: entry.type,
            description: entry.description || null,
          };
        });

        // Create the materialization
        const { data: materializationData, error: materializationError } =
          await supabase
            .from("materialization")
            .insert({
              run_id: runData.id,
              org_id: runData.org_id,
              dataset_id: runData.dataset_id,
              step_id: stepId,
              schema: dbSafeSchema,
              created_at: new Date().toISOString(),
              table_id: tableId,
              warehouse_fqn: warehouseFqn,
            })
            .select()
            .single();
        if (materializationError || !materializationData) {
          throw ServerErrors.internal(
            `Failed to create materialization for step ${stepId}`,
          );
        }
        return {
          message: "Created materialization",
          success: true,
          materialization: materializationData,
        };
      },
    }),
    savePublishedNotebookHtml: systemMutation({
      inputSchema: SavePublishedNotebookHtmlSchema,
      resolver: async (input) => {
        const supabase = createAdminClient();

        const { notebookId, htmlContent } = input;

        console.log("Encoded", htmlContent);

        // Decode base64 content
        const byteArray = Buffer.from(htmlContent, "base64");

        const { data: notebook } = await supabase
          .from("notebooks")
          .select("org_id")
          .eq("id", notebookId)
          .single();
        if (!notebook) {
          throw ResourceErrors.notFound(`Notebook ${notebookId} not found`);
        }
        const filePath = generatePublishedNotebookPath(
          notebookId,
          notebook.org_id,
        );
        // Save the HTML content to Supabase Storage
        const { data: uploadData, error: uploadError } = await supabase.storage
          .from("published-notebooks")
          .upload(filePath, byteArray, {
            upsert: true,
            contentType: "text/html",
            headers: {
              "Content-Encoding": "gzip",
            },
            // 5 Minute CDN cache. We will also cache on Vercel side to control it with revalidateTag
            cacheControl: "300",
          });
        if (uploadError || !uploadData) {
          throw ServerErrors.internal(
            `Failed to upload published notebook HTML for notebook ${notebookId}: ${uploadError.message}`,
          );
        }

        // Update the published_notebooks table with the new data path
        const { data: publishedNotebook, error: upsertError } = await supabase
          .from("published_notebooks")
          .upsert(
            {
              notebook_id: notebookId,
              data_path: filePath,
              updated_at: new Date().toISOString(),
              deleted_at: null,
            },
            { onConflict: "notebook_id" },
          )
          .select("id")
          .single();

        if (upsertError || !publishedNotebook) {
          throw ServerErrors.internal(
            `Failed to update published_notebooks for notebook ${notebookId}: ${upsertError.message}`,
          );
        }

        revalidateTag(publishedNotebook.id);
        return {
          message: "Saved published notebook HTML",
          success: true,
        };
      },
    }),
  },
  Query: {
    system: async (_: unknown, _args: unknown, context: GraphQLContext) => {
      if (!context.systemCredentials) {
        throw AuthenticationErrors.notAuthorized();
      }
      return {};
    },
  },
  System: {
    resolveTables: async (
      _: unknown,
      input: {
        references: string[];
        metadata?: { orgName?: string; datasetName?: string };
      },
      context: GraphQLContext,
    ) => {
      if (!context.systemCredentials) {
        throw AuthenticationErrors.notAuthorized();
      }

      const { references, metadata } = validateInput(
        ResolveTablesSchema,
        input,
      );

      const supabase = createAdminClient();

      const tableResolvers = [
        new LegacyInferredTableResolver(),
        ...(metadata?.orgName ? [new MetadataInferredTableResolver()] : []),
        new DBTableResolver(supabase, [
          (table) => {
            // If the catalog is iceberg return the table as is
            if (table.catalog === "iceberg") {
              return table;
            }
            return null;
          },
          (table) => {
            // If the catalog has a double underscore in the name we assume it's a
            // legacy private connector catalog and return the table as is
            if (table.catalog.includes("__")) {
              return table;
            }
            return null;
          },
        ]),
      ];

      let tableResolutionMap: TableResolutionMap = {};
      for (const ref of references) {
        tableResolutionMap[ref] = Table.fromString(ref);
      }

      for (const resolver of tableResolvers) {
        tableResolutionMap = await resolver.resolveTables(tableResolutionMap, {
          orgName: metadata?.orgName,
          datasetName: metadata?.datasetName,
        });
      }

      const results = Object.entries(tableResolutionMap).map(
        ([ref, table]) => ({
          reference: ref,
          fqn: table.toFQN(),
        }),
      );

      return results;
    },
  },
};
