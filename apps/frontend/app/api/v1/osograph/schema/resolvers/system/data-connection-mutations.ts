import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import { getSystemClient } from "@/app/api/v1/osograph/utils/access-control";
import {
  ResourceErrors,
  ServerErrors,
} from "@/app/api/v1/osograph/utils/errors";
import {
  CreateDataConnectionDatasets,
  validateInput,
} from "@/app/api/v1/osograph/utils/validation";
import { generateTableId } from "@/app/api/v1/osograph/utils/model";
import { getCatalogName } from "@/lib/dynamic-connectors";
import type { MutationCreateDataConnectionDatasetsArgs } from "@/lib/graphql/generated/graphql";
import type { MaterializationRow } from "@/lib/types/schema-types";
import { logger } from "@/lib/logger";

export const dataConnectionMutationResolvers: GraphQLResolverModule<GraphQLContext> =
  {
    Mutation: {
      createDataConnectionDatasets: async (
        _: unknown,
        args: MutationCreateDataConnectionDatasetsArgs,
        context: GraphQLContext,
      ) => {
        const client = getSystemClient(context);

        const { runId, orgId, dataConnectionId, schemas } = validateInput(
          CreateDataConnectionDatasets,
          args.input,
        );

        const { data: runData, error: runError } = await client
          .from("run")
          .select("requested_by")
          .eq("id", runId)
          .single();

        if (runError || !runData) {
          logger.error(`Run ${runId} not found: ${runError?.message}`);
          throw ResourceErrors.notFound("Run", runId);
        }

        const { data: dataConnection, error: dataConnectionError } =
          await client
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

        const { data: existingAliases, error: existingAliasError } =
          await client
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

        const createDataset = async (baseSchemaName: string) => {
          for (let index = 0; index < 100; index++) {
            const datasetName =
              index === 0 ? baseSchemaName : `${baseSchemaName}_${index}`;
            const { data, error: datasetError } = await client
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

            if (data && !datasetError) {
              return data;
            }
          }
          return null;
        };

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

        if (aliasesToCreate.length > 0) {
          const { error: aliasError } = await client
            .from("data_connection_alias")
            .insert(aliasesToCreate);

          if (aliasError) {
            logger.error("Failed to create aliases:", aliasError);
            throw ServerErrors.database("Failed to create aliases");
          }
        }

        const allDatasetIds = [
          ...createdDatasets.map((cd) => cd.dataset.id),
          ...Array.from(existingSchemaMap.values()).map(
            (alias) => alias.dataset_id,
          ),
        ];

        const { data: allExistingMats } =
          allDatasetIds.length > 0
            ? await client
                .from("materialization")
                .select("id, table_id, dataset_id")
                .in("dataset_id", allDatasetIds)
            : { data: [] };

        const existingMatsByDataset = new Map<string, Map<string, string>>();
        for (const mat of allExistingMats || []) {
          if (!existingMatsByDataset.has(mat.dataset_id)) {
            existingMatsByDataset.set(mat.dataset_id, new Map());
          }
          existingMatsByDataset.get(mat.dataset_id)!.set(mat.table_id, mat.id);
        }

        const materializationsToCreate = [];
        const materializationIdsToDelete = [];

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

          for (const table of schema.tables) {
            const tableId = generateTableId("DATA_CONNECTION", table.name);

            if (!existingMatsForDataset.has(tableId)) {
              const warehouseFqn = `${getCatalogName(
                dataConnection,
              )}.${schema.name}.${table.name}`;

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

          for (const [tableId, matId] of Array.from(
            existingMatsForDataset.entries(),
          )) {
            if (!inputTableIds.has(tableId)) {
              materializationIdsToDelete.push(matId);
            }
          }
        }

        const createdMaterializations: MaterializationRow[] = [];
        if (materializationsToCreate.length > 0) {
          const { data: matsData, error: matsError } = await client
            .from("materialization")
            .insert(materializationsToCreate)
            .select();

          if (matsError) {
            logger.error("Failed to create materializations:", matsError);
            throw ServerErrors.database("Failed to create materializations");
          }

          createdMaterializations.push(...matsData);
        }

        if (materializationIdsToDelete.length > 0) {
          const { error: deleteMatError } = await client
            .from("materialization")
            .delete()
            .in("id", materializationIdsToDelete);

          if (deleteMatError) {
            logger.error("Failed to delete materializations:", deleteMatError);
          }
        }

        const deletedDatasetIds = [];
        const datasetIdsToDelete = aliasesToDelete
          .map((alias) => alias.dataset_id)
          .filter((id) => id !== null);

        if (datasetIdsToDelete.length > 0) {
          const { error: deleteDatasetError } = await client
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
    },
  };
