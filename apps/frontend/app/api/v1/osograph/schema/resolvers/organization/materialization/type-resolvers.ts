import { getOrgScopedClient } from "@/app/api/v1/osograph/utils/access-control";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import { MaterializationRow } from "@/lib/types/schema-types";
import { logger } from "@/lib/logger";
import { ServerErrors } from "@/app/api/v1/osograph/utils/errors";

export const materializationTypeResolvers: GraphQLResolverModule<GraphQLContext> =
  {
    Materialization: {
      runId: (parent: MaterializationRow) => parent.run_id,
      run: async (
        parent: MaterializationRow,
        _args: unknown,
        context: GraphQLContext,
      ) => {
        const { client } = await getOrgScopedClient(context, parent.org_id);
        const { data, error } = await client
          .from("run")
          .select("*")
          .eq("id", parent.run_id)
          .single();
        if (error) {
          logger.error(
            `Error fetching run with id ${parent.run_id}: ${error.message}`,
          );
          throw ServerErrors.database(
            `Failed to fetch run with id ${parent.run_id}`,
          );
        }
        return data;
      },
      datasetId: (parent: MaterializationRow) => parent.dataset_id,
      createdAt: (parent: MaterializationRow) => parent.created_at,
      schema: (parent: MaterializationRow) => parent.schema,
    },
  };
