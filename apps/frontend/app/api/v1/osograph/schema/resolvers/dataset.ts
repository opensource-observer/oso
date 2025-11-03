import type { GraphQLResolverModule } from "@/app/api/v1/osograph/utils/types";
import {
  getOrganizationByName,
  requireAuthentication,
  requireOrgMembership,
  type GraphQLContext,
} from "@/app/api/v1/osograph/utils/auth";
import {
  AuthenticationErrors,
  ResourceErrors,
  ServerErrors,
} from "@/app/api/v1/osograph/utils/errors";
import { signTrinoJWT } from "@/lib/auth/auth";
import { getTrinoClient } from "@/lib/clients/trino";
import {
  Catalog,
  CatalogSchema,
  Column,
  ColumnSchema,
  Schema,
} from "@/lib/types/catalog";
import { logger } from "@/lib/logger";
import { assert } from "@opensource-observer/utils";
import { createAdminClient } from "@/lib/supabase/admin";
import { DatasetsRow } from "@/lib/types/schema-types";
import z from "zod";
import { validateInput } from "@/app/api/v1/osograph/utils/validation";
import { v4 as uuidv4 } from "uuid";

const TRINO_SCHEMA_TIMEOUT = 10000; // 10 seconds

export const datasetResolver: GraphQLResolverModule<GraphQLContext> = {
  Query: {
    osoApp_orgDatasets: async (
      _: unknown,
      { orgName }: { orgName: string },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const organization = await getOrganizationByName(orgName);
      await requireOrgMembership(authenticatedUser.userId, organization.id);

      const trinoJwt = await signTrinoJWT({
        ...authenticatedUser,
        orgId: organization.id,
        orgName: organization.org_name,
        orgRole: "member",
      });

      const trino = getTrinoClient(trinoJwt);

      const { data: catalogsResult, error } =
        await trino.queryAll("SHOW CATALOGS");
      if (error || !catalogsResult) {
        logger.error(
          `Failed to fetch catalogs for user ${authenticatedUser.userId}:`,
          error.message,
        );
        throw ServerErrors.externalService("Failed to fetch catalogs");
      }

      const results = await Promise.all(
        catalogsResult
          .flatMap((catalog) => catalog.data)
          .map(
            async (catalog: string[] | undefined): Promise<Catalog | null> => {
              if (!catalog || catalog.length === 0) {
                return null;
              }
              const catalogName = catalog[0];

              const query = `
        SELECT table_schema, table_name
        FROM ${catalogName}.information_schema.tables
        WHERE ${catalogName === "iceberg" ? "table_schema = 'oso'" : "table_schema != 'information_schema'"}
      `;
              try {
                const queryPromise = trino.queryAll(query);
                const timeoutPromise = new Promise<{
                  data: null;
                  error: Error;
                }>((resolve) =>
                  setTimeout(
                    () => resolve({ data: null, error: new Error("Timeout") }),
                    TRINO_SCHEMA_TIMEOUT,
                  ),
                );
                const { data: tablesResult, error } = await Promise.race([
                  queryPromise,
                  timeoutPromise,
                ]);
                if (error || !tablesResult) {
                  logger.warn(
                    `Could not query tables for catalog ${catalogName}:`,
                    error?.message,
                  );
                  return null;
                }
                const schemas: Record<string, Schema> = {};
                for (const table of tablesResult.flatMap((t) => t.data)) {
                  if (!table || table.length < 2) continue;
                  const [schemaName, tableName] = table;
                  assert(
                    typeof schemaName === "string" &&
                      typeof tableName === "string",
                    "Invalid table metadata",
                  );
                  if (!schemas[schemaName]) {
                    schemas[schemaName] = { name: schemaName, tables: [] };
                  }
                  schemas[schemaName].tables.push({
                    name: tableName,
                  });
                }
                return CatalogSchema.parse({
                  name: catalogName,
                  schemas: Object.values(schemas),
                });
              } catch (error) {
                logger.warn(
                  `Could not query tables for catalog ${catalogName}:`,
                  error,
                );
                return null;
              }
            },
          ),
      );
      const filteredResults = results.filter(
        (result): result is Catalog => result !== null,
      );

      const datasets = await getOrganizationDatasets(organization.id);

      const tablesByCatalogAndSchema = filteredResults.reduce(
        (acc, catalog) => {
          for (const schema of catalog.schemas) {
            const key = `${catalog.name}.${schema.name}`;
            acc[key] = schema.tables;
          }
          return acc;
        },
        {} as Record<string, { name: string }[]>,
      );

      const response = datasets.map((dataset) => {
        const key = `${dataset.catalog}.${dataset.schema}`;
        return {
          ...dataset,
          tables: tablesByCatalogAndSchema[key] ?? [],
        };
      });

      return response;
    },

    osoApp_dataset: async (
      _: unknown,
      { orgName, datasetName }: { orgName: string; datasetName: string },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const organization = await getOrganizationByName(orgName);
      await requireOrgMembership(authenticatedUser.userId, organization.id);

      const supabase = createAdminClient();
      const { data, error } = await supabase
        .from("datasets")
        .select("*, models:model(*)")
        .eq("org_id", organization.id)
        .eq("name", datasetName)
        .is("deleted_at", null)
        .single();

      if (error) {
        throw ResourceErrors.notFound("Dataset", `name: ${datasetName}`);
      }

      return {
        ...data,
        tables: data.models.map((m) => ({ name: m.name })),
      };
    },

    osoApp_datasetTableMetadata: async (
      _: unknown,
      {
        orgName,
        catalogName,
        schemaName,
        tableName,
      }: {
        orgName: string;
        catalogName: string;
        schemaName: string;
        tableName: string;
      },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const organization = await getOrganizationByName(orgName);
      await requireOrgMembership(authenticatedUser.userId, organization.id);

      const trinoJwt = await signTrinoJWT({
        ...authenticatedUser,
        orgId: organization.id,
        orgName: organization.org_name,
        orgRole: "member",
      });

      const trino = getTrinoClient(trinoJwt);

      const query = `
        SELECT column_name, data_type, column_comment
        FROM ${catalogName}.information_schema.columns
        WHERE table_schema = '${schemaName}' AND table_name = '${tableName}'
      `;
      const { data: columnResult, error } = await trino.queryAll(query);
      if (error || !columnResult) {
        logger.error(
          `Failed to fetch catalogs for user ${authenticatedUser.userId}:`,
          error.message,
        );
        throw ServerErrors.externalService("Failed to fetch catalogs");
      }

      const results = await Promise.all(
        columnResult
          .flatMap((column) => column.data)
          .map(
            async (
              column: (string | null)[] | undefined,
            ): Promise<Column | null> => {
              if (!column || column.length !== 3) {
                return null;
              }
              const [columnName, columnType, columnComment] = column;
              return ColumnSchema.parse({
                name: columnName,
                type: columnType,
                description: columnComment ?? null,
              });
            },
          ),
      );
      const filteredResults = results.filter((result) => result !== null);
      return filteredResults;
    },
  },
  Mutation: {
    osoApp_createDataset: async (
      _: unknown,
      { input }: { input: z.infer<typeof CreateDatasetSchema> },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const validated = validateInput(CreateDatasetSchema, input);
      const organization = await getOrganizationByName(validated.orgName);
      await requireOrgMembership(authenticatedUser.userId, organization.id);

      const supabase = createAdminClient();
      const datasetId = uuidv4();
      let catalog: string;
      let schema: string;

      switch (validated.datasetType) {
        case "USER_MODEL":
          catalog = "user_iceberg";
          schema = `ds_${datasetId.replace(/-/g, "")}`;
          break;
        default:
          throw new Error(
            `Dataset type "${validated.datasetType}" is not supported yet.`,
          );
      }

      const { data: dataset, error } = await supabase
        .from("datasets")
        .insert({
          id: datasetId,
          org_id: organization.id,
          name: validated.name,
          display_name: validated.displayName,
          description: validated.description,
          catalog,
          schema,
          created_by: authenticatedUser.userId,
          is_public: validated.isPublic ?? false,
          dataset_type: validated.datasetType,
        })
        .select()
        .single();

      if (error) {
        logger.error("Failed to create dataset:", error);
        throw ServerErrors.database("Failed to create dataset");
      }

      return {
        dataset,
        message: "Dataset created successfully",
        success: true,
      };
    },
    osoApp_updateDataset: async (
      _: unknown,
      {
        datasetId,
        name,
        displayName,
        description,
        isPublic,
      }: {
        datasetId: string;
        name?: string;
        displayName?: string;
        description?: string;
        isPublic?: boolean;
      },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const supabase = createAdminClient();

      const { data: existingDataset, error: existingError } = await supabase
        .from("datasets")
        .select("org_id")
        .eq("id", datasetId)
        .single();

      if (existingError || !existingDataset) {
        throw AuthenticationErrors.notAuthorized();
      }

      await requireOrgMembership(
        authenticatedUser.userId,
        existingDataset.org_id,
      );

      const { data, error } = await supabase
        .from("datasets")
        .update({
          name,
          display_name: displayName,
          description,
          is_public: isPublic,
        })
        .eq("id", datasetId)
        .select()
        .single();

      if (error) {
        throw ServerErrors.database("Failed to update dataset");
      }

      return {
        dataset: data,
        message: "Dataset updated successfully",
        success: true,
      };
    },
  },
  Dataset: {
    id: (parent: DatasetsRow) => parent.id,
    orgId: (parent: DatasetsRow) => parent.org_id,
    createdAt: (parent: DatasetsRow) => parent.created_at,
    updatedAt: (parent: DatasetsRow) => parent.updated_at,
    deletedAt: (parent: DatasetsRow) => parent.deleted_at,
    name: (parent: DatasetsRow) => parent.name,
    displayName: (parent: DatasetsRow) => parent.display_name,
    description: (parent: DatasetsRow) => parent.description,
    catalog: (parent: DatasetsRow) => parent.catalog,
    schema: (parent: DatasetsRow) => parent.schema,
    createdBy: (parent: DatasetsRow) => parent.created_by,
    isPublic: (parent: DatasetsRow) => parent.is_public,
    datasetType: (parent: DatasetsRow) => parent.dataset_type,
  },
};

export const CreateDatasetSchema = z.object({
  orgName: z.string().min(1, "Organization name is required"),
  name: z
    .string()
    .min(1, "Dataset name is required")
    .regex(
      /^[a-zA-Z][a-zA-Z0-9_]+$/,
      "Dataset name can only contain letters, numbers, and underscores",
    ),
  displayName: z.string().min(1, "Display name is required"),
  description: z.string().optional(),
  isPublic: z.boolean().optional(),
  datasetType: z.enum(["USER_MODEL", "DATA_CONNECTOR", "DATA_INGESTION"]),
});

async function getOrganizationDatasets(orgId: string): Promise<DatasetsRow[]> {
  const supabase = createAdminClient();

  const { data, error } = await supabase
    .from("datasets_by_organization")
    .select("datasets(*)")
    .eq("org_id", orgId)
    .is("deleted_at", null);

  if (error) {
    throw ResourceErrors.notFound("Datasets", `org_id: ${orgId}`);
  }

  const { data: ownedDatasets, error: ownedError } = await supabase
    .from("datasets")
    .select("*")
    .eq("org_id", orgId)
    .is("deleted_at", null);

  if (ownedError) {
    throw ResourceErrors.notFound("Datasets", `org_id: ${orgId}`);
  }

  return data.map((d) => d.datasets).concat(ownedDatasets);
}
