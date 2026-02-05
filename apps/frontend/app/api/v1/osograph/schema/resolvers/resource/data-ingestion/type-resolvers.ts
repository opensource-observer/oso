import { getOrgResourceClient } from "@/app/api/v1/osograph/utils/access-control";
import { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { ServerErrors } from "@/app/api/v1/osograph/utils/errors";
import { getMaterializations } from "@/app/api/v1/osograph/utils/resolver-helpers";
import { logger } from "@/lib/logger";
import { DataIngestionsRow } from "@/lib/types/schema-types";
import { getModelContext } from "@/app/api/v1/osograph/schema/resolvers/model-context";
import type { FilterableConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import { generateTableId } from "@/app/api/v1/osograph/utils/model";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";

/**
 * Type resolvers for DataIngestion.
 * These field resolvers don't require auth checks as they operate on
 * already-fetched data ingestion data.
 */
export const dataIngestionTypeResolvers: GraphQLResolverModule<GraphQLContext> =
  {
    DataIngestion: {
      id: (parent: DataIngestionsRow) => parent.id,
      async orgId(
        parent: DataIngestionsRow,
        _args: unknown,
        context: GraphQLContext,
      ) {
        const { client } = await getOrgResourceClient(
          context,
          "data_ingestion",
          parent.id,
        );
        const { data: dataset, error } = await client
          .from("datasets")
          .select("org_id")
          .eq("id", parent.dataset_id)
          .single();

        if (error || !dataset) {
          logger.error(
            `Error fetching dataset for data ingestion ${parent.id}: ${error?.message}`,
          );
          throw ServerErrors.database("Failed to fetch dataset");
        }

        return dataset.org_id;
      },
      datasetId: (parent: DataIngestionsRow) => parent.dataset_id,
      factoryType: (parent: DataIngestionsRow) => parent.factory_type,
      config: (parent: DataIngestionsRow) => parent.config,
      createdAt: (parent: DataIngestionsRow) => parent.created_at,
      updatedAt: (parent: DataIngestionsRow) => parent.updated_at,
      modelContext: async (
        parent: DataIngestionsRow,
        // TODO(jabolo): Find the correct type from @/lib/graphql/generated/graphql
        // eslint-disable-next-line oso-frontend/type-safety/no-inline-resolver-types
        args: { tableName: string },
      ) => {
        return getModelContext(parent.dataset_id, args.tableName);
      },
      materializations: async (
        parent: DataIngestionsRow,
        args: FilterableConnectionArgs & { tableName: string },
        context: GraphQLContext,
      ) => {
        const { tableName, ...restArgs } = args;
        return getMaterializations(
          restArgs,
          context,
          parent.org_id,
          parent.dataset_id,
          generateTableId("DATA_INGESTION", tableName),
        );
      },
    },
  };
