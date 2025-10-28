import type { GraphQLResolverModule } from "@/app/api/v1/osograph/utils/types";
import {
  getOrganizationByName,
  requireAuthentication,
  requireOrgMembership,
  type GraphQLContext,
} from "@/app/api/v1/osograph/utils/auth";
import { ServerErrors } from "@/app/api/v1/osograph/utils/errors";
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

export const catalogResolvers: GraphQLResolverModule<GraphQLContext> = {
  Query: {
    osoApp_myCatalogs: async (
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
              console.log("Processing catalog:", catalogName);

              const query = `
        SELECT table_schema, table_name
        FROM ${catalogName}.information_schema.tables
        WHERE ${catalogName === "iceberg" ? "table_schema = 'oso'" : "table_schema != 'information_schema'"}
      `;
              try {
                const { data: tablesResult, error } =
                  await trino.queryAll(query);
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
      const filteredResults = results.filter((result) => result !== null);
      return filteredResults;
    },

    osoApp_tableColumns: async (
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
              console.log("column:", columnName, columnType, columnComment);
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
};
