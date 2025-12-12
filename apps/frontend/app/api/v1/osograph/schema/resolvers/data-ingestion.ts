import { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import {
  CreateDataIngestionConfigSchema,
  validateInput,
} from "@/app/api/v1/osograph/utils/validation";
import { requireAuthentication } from "@/app/api/v1/osograph/utils/auth";
import { checkMembershipExists } from "@/app/api/v1/osograph/utils/resolver-helpers";
import { createAdminClient } from "@/lib/supabase/admin";
import {
  AuthenticationErrors,
  ResourceErrors,
  ServerErrors,
} from "@/app/api/v1/osograph/utils/errors";
import { logger } from "@/lib/logger";
import z from "zod";
import type { FilterableConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import { DataIngestionsRow } from "@/lib/types/schema-types";
import { buildConnectionOrEmpty } from "@/app/api/v1/osograph/utils/resolver-helpers";

export const dataIngestionResolvers = {
  Mutation: {
    async createDataIngestionConfig(
      _: unknown,
      args: { input: z.infer<typeof CreateDataIngestionConfigSchema> },
      context: GraphQLContext,
    ) {
      const authenticatedUser = requireAuthentication(context.user);
      const input = validateInput(CreateDataIngestionConfigSchema, args.input);
      const supabase = createAdminClient();

      const { data: dataset, error: datasetError } = await supabase
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

      if (
        !(await checkMembershipExists(authenticatedUser.userId, dataset.org_id))
      ) {
        throw AuthenticationErrors.notAuthorized();
      }

      const { data: config, error: configError } = await supabase
        .from("data_ingestions")
        .insert({
          dataset_id: input.datasetId,
          factory_type: input.factoryType,
          config: input.config,
        })
        .select()
        .single();

      if (configError || !config) {
        logger.error(
          `Error creating data ingestion config: ${configError?.message}`,
        );
        throw ServerErrors.database("Failed to create data ingestion config");
      }

      // Return the raw row so the `DataIngestionConfig` field resolvers (which
      // expect snake_case columns) can resolve non-null GraphQL fields.
      return config as DataIngestionsRow;
    },
  },

  DataIngestionConfig: {
    id: (parent: DataIngestionsRow) => parent.id,
    datasetId: (parent: DataIngestionsRow) => parent.dataset_id,
    factoryType: (parent: DataIngestionsRow) => parent.factory_type,
    config: (parent: DataIngestionsRow) => parent.config,
    createdAt: (parent: DataIngestionsRow) => parent.created_at,
    updatedAt: (parent: DataIngestionsRow) => parent.updated_at,
  },

  DataIngestion: {
    orgId: (parent: { org_id: string }) => parent.org_id,
    datasetId: (parent: { dataset_id: string }) => parent.dataset_id,
    configs: async (
      parent: { dataset_id: string; org_id: string },
      args: FilterableConnectionArgs,
    ) => {
      const supabase = createAdminClient();

      const {
        data: configs,
        error,
        count,
      } = await supabase
        .from("data_ingestions")
        .select("*", { count: "exact" })
        .eq("dataset_id", parent.dataset_id)
        .is("deleted_at", null)
        .order("created_at", { ascending: false });

      if (error) {
        logger.error(`Error fetching data ingestion configs: ${error.message}`);
        throw ServerErrors.database("Failed to fetch data ingestion configs");
      }

      return buildConnectionOrEmpty(configs, args, count);
    },
  },
};
