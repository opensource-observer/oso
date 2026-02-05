import { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import {
  CreateDataIngestionSchema,
  validateInput,
} from "@/app/api/v1/osograph/utils/validation";
import { getOrgScopedClient } from "@/app/api/v1/osograph/utils/access-control";
import {
  ResourceErrors,
  ServerErrors,
} from "@/app/api/v1/osograph/utils/errors";
import { logger } from "@/lib/logger";
import { DataIngestionsRow } from "@/lib/types/schema-types";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import { MutationCreateDataIngestionConfigArgs } from "@/lib/graphql/generated/graphql";

/**
 * Data ingestion mutations that operate at organization scope.
 * These resolvers use getOrgScopedClient because they don't have a resourceId yet.
 */
export const dataIngestionMutations: GraphQLResolverModule<GraphQLContext>["Mutation"] =
  {
    async createDataIngestionConfig(
      _: unknown,
      args: MutationCreateDataIngestionConfigArgs,
      context: GraphQLContext,
    ) {
      const input = validateInput(CreateDataIngestionSchema, args.input);

      // TODO(jabolo): This is incorrect, dataset id is not an org id
      const { client } = await getOrgScopedClient(context, input.datasetId);

      const { data: dataset, error: datasetError } = await client
        .from("datasets")
        .select("*")
        .eq("id", input.datasetId)
        .single();

      if (datasetError || !dataset) {
        logger.error(
          `Error fetching dataset with id ${input.datasetId}: ${datasetError?.message}`,
        );
        throw ResourceErrors.notFound("Dataset not found");
      }

      const { client: orgClient } = await getOrgScopedClient(
        context,
        dataset.org_id,
      );

      const { data: existingConfig } = await orgClient
        .from("data_ingestions")
        .select("id")
        .eq("dataset_id", input.datasetId)
        .is("deleted_at", null)
        .maybeSingle();

      const { data: config, error: configError } = existingConfig
        ? await orgClient
            .from("data_ingestions")
            .update({
              factory_type: input.factoryType,
              config: input.config,
            })
            .eq("id", existingConfig.id)
            .select()
            .single()
        : await orgClient
            .from("data_ingestions")
            .insert({
              dataset_id: input.datasetId,
              factory_type: input.factoryType,
              config: input.config,
              org_id: dataset.org_id,
              name: dataset.name,
            })
            .select()
            .single();

      if (configError || !config) {
        logger.error(
          `Error creating data ingestion config: ${configError?.message}`,
        );
        throw ServerErrors.database("Failed to create data ingestion config");
      }

      // Return the raw row so the `DataIngestion` field resolvers can
      // access snake_case database columns and resolve GraphQL fields.
      return config as DataIngestionsRow;
    },
  };
