import { logger } from "@/lib/logger";
import { ServerErrors } from "@/app/api/v1/osograph/utils/errors";
import { MutationResolvers } from "@/app/api/v1/osograph/types/generated/types";
import { createResolversCollection } from "@/app/api/v1/osograph/utils/resolver-builder";
import {
  withValidation,
  withOrgScopedClient,
} from "@/app/api/v1/osograph/utils/resolver-middleware";
import { CreateDataModelInputSchema } from "@/app/api/v1/osograph/types/generated/validation";

type DataModelMutationResolvers = Pick<
  Required<MutationResolvers>,
  "createDataModel"
>;

/**
 * Data model mutations that operate at organization scope.
 * These resolvers use withOrgScopedClient because they don't have a resourceId yet.
 */
export const dataModelMutations =
  createResolversCollection<DataModelMutationResolvers>()
    .defineWithBuilder("createDataModel", (builder) => {
      return builder
        .use(withValidation(CreateDataModelInputSchema()))
        .use(withOrgScopedClient(({ args }) => args.input.orgId))
        .resolve(async (_, { input }, context) => {
          const { data, error } = await context.client
            .from("model")
            .insert({
              org_id: input.orgId,
              dataset_id: input.datasetId,
              name: input.name,
              is_enabled: input.isEnabled ?? undefined,
            })
            .select()
            .single();

          if (error) {
            logger.error("Failed to create dataModel:", error);
            throw ServerErrors.database("Failed to create dataModel");
          }

          return {
            success: true,
            message: "DataModel created successfully",
            dataModel: data,
          };
        });
    })
    .resolvers();
