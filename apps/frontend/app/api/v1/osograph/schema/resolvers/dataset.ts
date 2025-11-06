import { v4 as uuidv4 } from "uuid";
import { createAdminClient } from "@/lib/supabase/admin";
import { signTrinoJWT } from "@/lib/auth/auth";
import { getTrinoClient } from "@/lib/clients/trino";
import { logger } from "@/lib/logger";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import {
  getOrganization,
  getOrganizationByName,
  getUserProfile,
  requireAuthentication,
  requireOrgMembership,
} from "@/app/api/v1/osograph/utils/auth";
import { validateInput } from "@/app/api/v1/osograph/utils/validation";
import { CreateDatasetSchema } from "@/app/api/v1/osograph/utils/validation";
import {
  ResourceErrors,
  ServerErrors,
} from "@/app/api/v1/osograph/utils/errors";
import {
  buildConnection,
  emptyConnection,
} from "@/app/api/v1/osograph/utils/connection";
import type { ConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import {
  getFetchLimit,
  getSupabaseRange,
} from "@/app/api/v1/osograph/utils/pagination";
import {
  Catalog,
  CatalogSchema,
  Column,
  ColumnSchema,
  Schema,
} from "@/lib/types/catalog";
import z from "zod";
import { assert } from "@opensource-observer/utils";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";

const TRINO_SCHEMA_TIMEOUT = 10_000; // 10 seconds

export const datasetResolvers: GraphQLResolverModule<GraphQLContext> = {
  Query: {
    datasets: async (
      _: unknown,
      args: ConnectionArgs,
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const supabase = createAdminClient();

      const { data: memberships } = await supabase
        .from("users_by_organization")
        .select("org_id")
        .eq("user_id", authenticatedUser.userId)
        .is("deleted_at", null);

      const orgIds = memberships?.map((m) => m.org_id) || [];
      if (orgIds.length === 0) {
        return emptyConnection();
      }

      const trinoJwt = await signTrinoJWT({
        ...authenticatedUser,
        orgId: orgIds[0],
        orgName: "",
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
        WHERE ${
          catalogName === "iceberg"
            ? "table_schema = 'oso'"
            : "table_schema != 'information_schema'"
        }
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

      const limit = getFetchLimit(args);
      const [start, end] = getSupabaseRange({
        ...args,
        first: limit,
      });

      const { data: datasetsList, error: datasetError } = await supabase
        .from("datasets")
        .select("*")
        .in("org_id", orgIds)
        .is("deleted_at", null)
        .range(start, end);

      if (datasetError) {
        logger.error(`Failed to fetch datasets: ${datasetError}`);
        throw ServerErrors.database("Failed to fetch datasets");
      }

      if (!datasetsList || datasetsList.length === 0) {
        return emptyConnection();
      }

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

      const response = datasetsList.map((dataset) => {
        const key = `${dataset.catalog}.${dataset.schema}`;
        return {
          ...dataset,
          tables: tablesByCatalogAndSchema[key] ?? [],
        };
      });

      return buildConnection(response, args);
    },

    dataset: async (
      _: unknown,
      args: { id?: string; name?: string },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const supabase = createAdminClient();

      if (!args.id && !args.name) {
        return null;
      }

      let query = supabase.from("datasets").select("*").is("deleted_at", null);

      if (args.id) {
        query = query.eq("id", args.id);
      } else if (args.name) {
        query = query.eq("name", args.name);
      }

      const { data: dataset, error } = await query.single();

      if (error || !dataset) {
        return null;
      }

      try {
        await requireOrgMembership(authenticatedUser.userId, dataset.org_id);
        return dataset;
      } catch {
        return null;
      }
    },

    datasetTableMetadata: async (
      _: unknown,
      args: {
        orgId: string;
        catalogName: string;
        schemaName: string;
        tableName: string;
      },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const org = await getOrganization(args.orgId);
      await requireOrgMembership(authenticatedUser.userId, org.id);

      const trinoJwt = await signTrinoJWT({
        ...authenticatedUser,
        orgId: org.id,
        orgName: org.org_name,
        orgRole: "member",
      });

      const trino = getTrinoClient(trinoJwt);

      const query = `
        SELECT column_name, data_type, column_comment
        FROM ${args.catalogName}.information_schema.columns
        WHERE table_schema = '${args.schemaName}' AND table_name = '${args.tableName}'
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
    createDataset: async (
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

    updateDataset: async (
      _: unknown,
      args: {
        input: {
          id: string;
          name?: string;
          displayName?: string;
          description?: string;
          isPublic?: boolean;
        };
      },
      context: GraphQLContext,
    ) => {
      const authenticatedUser = requireAuthentication(context.user);
      const { input } = args;

      const supabase = createAdminClient();

      const { data: existingDataset, error: existingError } = await supabase
        .from("datasets")
        .select("org_id")
        .eq("id", input.id)
        .single();

      if (existingError || !existingDataset) {
        throw ResourceErrors.notFound("Dataset", input.id);
      }

      await requireOrgMembership(
        authenticatedUser.userId,
        existingDataset.org_id,
      );

      const { data, error } = await supabase
        .from("datasets")
        .update(input)
        .eq("id", input.id)
        .select()
        .single();

      if (error) {
        throw ServerErrors.database(
          `Failed to update dataset: ${error.message}`,
        );
      }

      return {
        dataset: data,
        message: "Dataset updated successfully",
        success: true,
      };
    },
  },

  Dataset: {
    displayName: (parent: { display_name: string | null }) =>
      parent.display_name,
    createdAt: (parent: { created_at: string }) => parent.created_at,
    updatedAt: (parent: { updated_at: string }) => parent.updated_at,
    creatorId: (parent: { created_by: string }) => parent.created_by,
    orgId: (parent: { org_id: string }) => parent.org_id,
    isPublic: (parent: { is_public: boolean }) => parent.is_public,
    type: (parent: { dataset_type: string }) => parent.dataset_type,

    creator: async (parent: { created_by: string }) => {
      return getUserProfile(parent.created_by);
    },

    organization: async (parent: { org_id: string }) => {
      return getOrganization(parent.org_id);
    },
  },
};
