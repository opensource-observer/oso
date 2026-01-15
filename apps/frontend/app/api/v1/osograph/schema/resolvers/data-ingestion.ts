import { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import {
  CreateDataIngestionSchema,
  validateInput,
  MaterializationWhereSchema,
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
import { DataIngestionsRow } from "@/lib/types/schema-types";
import { FilterableConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import { queryWithPagination } from "@/app/api/v1/osograph/utils/query-helpers";

export const dataIngestionResolvers = {
  Mutation: {
    async createDataIngestionConfig(
      _: unknown,
      args: { input: z.infer<typeof CreateDataIngestionSchema> },
      context: GraphQLContext,
    ) {
      const authenticatedUser = requireAuthentication(context.user);
      const input = validateInput(CreateDataIngestionSchema, args.input);
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

      const { data: existingConfig } = await supabase
        .from("data_ingestions")
        .select("id")
        .eq("dataset_id", input.datasetId)
        .is("deleted_at", null)
        .maybeSingle();

      const { data: config, error: configError } = existingConfig
        ? await supabase
            .from("data_ingestions")
            .update({
              factory_type: input.factoryType,
              config: input.config,
            })
            .eq("id", existingConfig.id)
            .select()
            .single()
        : await supabase
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
  },

  DataIngestion: {
    id: (parent: DataIngestionsRow) => parent.id,
    async orgId(parent: DataIngestionsRow) {
      const supabase = createAdminClient();
      const { data: dataset, error } = await supabase
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
    materializations: async (
      parent: DataIngestionsRow,
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      return queryWithPagination(args, context, {
        tableName: "materialization",
        whereSchema: MaterializationWhereSchema,
        requireAuth: false,
        filterByUserOrgs: false,
        parentOrgIds: parent.org_id,
        basePredicate: {
          eq: [{ key: "dataset_id", value: parent.dataset_id }],
        },
        orderBy: {
          key: "created_at",
          ascending: false,
        },
      });
    },
  },
};
