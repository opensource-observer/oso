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
  CreateDataConnectionDatasets,
} from "@/app/api/v1/osograph/utils/validation";
import z from "zod";
import { logger } from "@/lib/logger";
import { Json } from "@/lib/types/supabase";
import { generatePublishedNotebookPath } from "@/lib/notebook/utils";
import { revalidateTag } from "next/cache";
import {
  generateTableId,
  validateTableId,
} from "@/app/api/v1/osograph/utils/model";
import { getCatalogName } from "@/lib/dynamic-connectors";
import { MaterializationRow } from "@/lib/types/schema-types";

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
          throw ResourceErrors.notFound("Run", runId);
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
          throw ResourceErrors.notFound("Run", runId);
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
          throw ResourceErrors.notFound("Run", runId);
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
          throw ResourceErrors.notFound("Run", runId);
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
          throw ResourceErrors.notFound("Step", stepId);
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
        validateTableId(tableId);

        logger.info(`Creating materialization for step ${stepId}`);

        // Get the step
        const { data: stepData, error: stepError } = await supabase
          .from("step")
          .select("*")
          .eq("id", stepId)
          .single();
        if (stepError || !stepData) {
          logger.error(`Step ${stepId} not found: ${stepError?.message}`);
          throw ResourceErrors.notFound("Step", stepId);
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
          throw ResourceErrors.notFound("Run for step", stepId);
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
          throw ResourceErrors.notFound("Notebook", notebookId);
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

    createDataConnectionDatasets: systemMutation({
      inputSchema: CreateDataConnectionDatasets,
      resolver: async (input) => {
        const { runId, orgId, dataConnectionId, schemas } = validateInput(
          CreateDataConnectionDatasets,
          input,
        );
        const supabase = createAdminClient();

        const { data: runData, error: runError } = await supabase
          .from("run")
          .select("requested_by")
          .eq("id", runId)
          .single();
        if (runError || !runData) {
          logger.error(`Run ${runId} not found: ${runError?.message}`);
          throw ResourceErrors.notFound("Run", runId);
        }

        const { data: dataConnection, error: dataConnectionError } =
          await supabase
            .from("dynamic_connectors")
            .select("*")
            .eq("id", dataConnectionId)
            .single();
        if (dataConnectionError || !dataConnection) {
          logger.error(
            `Data connection ${dataConnectionId} not found: ${dataConnectionError?.message}`,
          );
          throw ResourceErrors.notFound("Dynamic Connector", dataConnectionId);
        }

        // Get all existing aliases for this data connection
        const { data: existingAliases, error: existingAliasError } =
          await supabase
            .from("data_connection_alias")
            .select("*, datasets(*)")
            .eq("org_id", orgId)
            .eq("data_connection_id", dataConnectionId);

        if (existingAliasError) {
          logger.error("Failed to fetch existing aliases:", existingAliasError);
          throw ServerErrors.database("Failed to fetch existing aliases");
        }

        const schemasSet = new Set(schemas.map((schema) => schema.name));
        const existingSchemaMap = new Map(
          (existingAliases || []).map((alias) => [alias.schema_name, alias]),
        );

        const schemasToCreate = schemas.filter(
          (schema) => !existingSchemaMap.has(schema.name),
        );
        const aliasesToDelete = (existingAliases || []).filter(
          (alias) => !schemasSet.has(alias.schema_name),
        );

        // Helper function to create a dataset with a unique name
        const createDataset = async (baseSchemaName: string) => {
          for (let index = 0; index < 100; index++) {
            const datasetName =
              index === 0 ? baseSchemaName : `${baseSchemaName}_${index}`;
            const { data, error: datasetError } = await supabase
              .from("datasets")
              .insert({
                org_id: orgId,
                name: datasetName,
                display_name: datasetName,
                dataset_type: "DATA_CONNECTION",
                created_by: runData.requested_by || "system",
              })
              .select()
              .single();

            if (!!data && !datasetError) {
              return data;
            }
          }
          return null;
        };

        // Create datasets and collect aliases to create
        const createdDatasets = [];
        const aliasesToCreate = [];

        for (const schema of schemasToCreate) {
          const dataset = await createDataset(schema.name);

          if (!dataset) {
            logger.error(`Failed to create dataset for schema ${schema.name}`);
            throw ServerErrors.database(
              `Failed to create dataset for schema ${schema.name} after multiple attempts`,
            );
          }

          createdDatasets.push({ dataset, schema });
          aliasesToCreate.push({
            org_id: orgId,
            dataset_id: dataset.id,
            data_connection_id: dataConnectionId,
            schema_name: schema.name,
          });
        }

        // Batch insert aliases
        if (aliasesToCreate.length > 0) {
          const { error: aliasError } = await supabase
            .from("data_connection_alias")
            .insert(aliasesToCreate);

          if (aliasError) {
            logger.error("Failed to create aliases:", aliasError);
            throw ServerErrors.database("Failed to create aliases");
          }
        }

        // Get all existing materializations for all schemas in one query
        const allDatasetIds = [
          ...createdDatasets.map((cd) => cd.dataset.id),
          ...Array.from(existingSchemaMap.values()).map(
            (alias) => alias.dataset_id,
          ),
        ];

        const { data: allExistingMats } =
          allDatasetIds.length > 0
            ? await supabase
                .from("materialization")
                .select("id, table_id, dataset_id")
                .in("dataset_id", allDatasetIds)
            : { data: [] };

        // Group existing materializations by dataset_id
        const existingMatsByDataset = new Map<string, Map<string, string>>();
        for (const mat of allExistingMats || []) {
          if (!existingMatsByDataset.has(mat.dataset_id)) {
            existingMatsByDataset.set(mat.dataset_id, new Map());
          }
          existingMatsByDataset.get(mat.dataset_id)!.set(mat.table_id, mat.id);
        }

        // Collect all materializations to create and IDs to delete
        const materializationsToCreate = [];
        const materializationIdsToDelete = [];

        // Process all schemas (both new and existing)
        for (const schema of schemas) {
          const datasetId =
            createdDatasets.find((cd) => cd.schema.name === schema.name)
              ?.dataset.id || existingSchemaMap.get(schema.name)?.dataset_id;
          if (!datasetId) {
            logger.error(`Dataset ID not found for schema ${schema.name}`);
            throw ServerErrors.internal(
              `Dataset ID not found for schema ${schema.name}`,
            );
          }

          const existingMatsForDataset =
            existingMatsByDataset.get(datasetId) || new Map();
          const inputTableIds = new Set(
            schema.tables.map((t) => `${schema.name}.${t.name}`),
          );

          // Create materializations for new tables
          for (const table of schema.tables) {
            const tableId = generateTableId("DATA_CONNECTION", table.name);

            if (!existingMatsForDataset.has(tableId)) {
              const warehouseFqn = `${getCatalogName(dataConnection)}.${schema.name}.${table.name}`;

              // Convert schema to db-safe format
              const dbSafeSchema = table.schema.map((col) => ({
                name: col.name,
                type: col.type,
                description: col.description || null,
              }));

              materializationsToCreate.push({
                run_id: runId,
                org_id: orgId,
                dataset_id: datasetId,
                step_id: null,
                schema: dbSafeSchema,
                table_id: tableId,
                warehouse_fqn: warehouseFqn,
              });
            }
          }

          // Collect materializations to delete
          for (const [tableId, matId] of Array.from(
            existingMatsForDataset.entries(),
          )) {
            if (!inputTableIds.has(tableId)) {
              materializationIdsToDelete.push(matId);
            }
          }
        }

        // Batch insert materializations
        const createdMaterializations: MaterializationRow[] = [];
        if (materializationsToCreate.length > 0) {
          const { data: matsData, error: matsError } = await supabase
            .from("materialization")
            .insert(materializationsToCreate)
            .select();

          if (matsError) {
            logger.error("Failed to create materializations:", matsError);
            throw ServerErrors.database("Failed to create materializations");
          }

          createdMaterializations.push(...matsData);
        }

        // Batch delete materializations
        if (materializationIdsToDelete.length > 0) {
          const { error: deleteMatError } = await supabase
            .from("materialization")
            .delete()
            .in("id", materializationIdsToDelete);

          if (deleteMatError) {
            logger.error("Failed to delete materializations:", deleteMatError);
          }
        }

        // Delete aliases and datasets that are no longer needed
        const deletedDatasetIds = [];
        const datasetIdsToDelete = aliasesToDelete
          .map((alias) => alias.dataset_id)
          .filter((id) => id !== null);

        if (datasetIdsToDelete.length > 0) {
          // Batch delete datasets
          const { error: deleteDatasetError } = await supabase
            .from("datasets")
            .delete()
            .in("id", datasetIdsToDelete);

          if (deleteDatasetError) {
            logger.error("Failed to delete datasets:", deleteDatasetError);
            throw ServerErrors.database("Failed to delete datasets");
          }

          deletedDatasetIds.push(...datasetIdsToDelete);
        }

        return {
          success: true,
          message: `Created ${createdDatasets.length} dataset(s), ${createdMaterializations.length} materialization(s), deleted ${deletedDatasetIds.length} dataset(s)`,
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
        new MetadataInferredTableResolver(),
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
