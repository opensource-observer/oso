import { ModelContextsRow } from "@/lib/types/schema-types";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";

/**
 * Type resolvers for ModelContext.
 * These field resolvers don't require auth checks as they operate on
 * already-fetched model context data.
 */
export const modelContextTypeResolvers: GraphQLResolverModule<GraphQLContext> =
  {
    ModelContext: {
      orgId: (parent: ModelContextsRow) => parent.org_id,
      datasetId: (parent: ModelContextsRow) => parent.dataset_id,
      tableId: (parent: ModelContextsRow) => parent.table_id,
      context: (parent: ModelContextsRow) => parent.context,
      columnContext: (parent: ModelContextsRow) => parent.column_context,
      createdAt: (parent: ModelContextsRow) => parent.created_at,
      updatedAt: (parent: ModelContextsRow) => parent.updated_at,
    },
  };
