import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import {
  ConnectionArgs,
  FilterableConnectionArgs,
} from "@/app/api/v1/osograph/utils/pagination";
import { StaticModelRow } from "@/lib/types/schema-types";
import {
  getOrganization,
  requireAuthentication,
} from "@/app/api/v1/osograph/utils/auth";
import {
  getMaterializations,
  getModelRunConnection,
  getResourceById,
} from "@/app/api/v1/osograph/utils/resolver-helpers";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import { getModelContext } from "@/app/api/v1/osograph/schema/resolvers/model-context";
import {
  executePreviewQuery,
  generateTableId,
} from "@/app/api/v1/osograph/utils/model";
import { getOrgResourceClient } from "@/app/api/v1/osograph/utils/access-control";
import type { PreviewData } from "@/lib/graphql/generated/graphql";

/**
 * Type resolvers for StaticModel.
 * These field resolvers don't require auth checks as they operate on
 * already-fetched static model data.
 */
export const staticModelTypeResolvers: GraphQLResolverModule<GraphQLContext> = {
  StaticModel: {
    orgId: (parent: StaticModelRow) => {
      return parent.org_id;
    },
    organization: async (
      parent: StaticModelRow,
      _args: unknown,
      context: GraphQLContext,
    ) => {
      const { client } = await getOrgResourceClient(
        context,
        "static_model",
        parent.id,
      );
      return getOrganization(parent.org_id, client);
    },
    dataset: async (
      parent: StaticModelRow,
      _args: unknown,
      context: GraphQLContext,
    ) => {
      const { client } = await getOrgResourceClient(
        context,
        "static_model",
        parent.id,
      );
      return getResourceById(
        {
          tableName: "datasets",
          id: parent.dataset_id,
          userId: "",
          checkMembership: false,
        },
        client,
      );
    },
    createdAt: (parent: StaticModelRow) => {
      return parent.created_at;
    },
    updatedAt: (parent: StaticModelRow) => {
      return parent.updated_at;
    },
    runs: async (
      parent: StaticModelRow,
      args: ConnectionArgs,
      context: GraphQLContext,
    ) => {
      const { client } = await getOrgResourceClient(
        context,
        "static_model",
        parent.id,
      );
      return getModelRunConnection(parent.dataset_id, parent.id, args, client);
    },
    modelContext: async (parent: StaticModelRow) => {
      return getModelContext(parent.dataset_id, parent.id);
    },
    materializations: async (
      parent: StaticModelRow,
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      return getMaterializations(
        args,
        context,
        parent.org_id,
        parent.dataset_id,
        generateTableId("STATIC_MODEL", parent.id),
      );
    },
    previewData: async (
      parent: StaticModelRow,
      _args: Record<string, never>,
      context: GraphQLContext,
    ): Promise<PreviewData> => {
      const authenticatedUser = requireAuthentication(context.user);
      const { client } = await getOrgResourceClient(
        context,
        "static_model",
        parent.id,
        "read",
      );

      const tableId = generateTableId("STATIC_MODEL", parent.id);

      return executePreviewQuery(
        parent.org_id,
        parent.dataset_id,
        tableId,
        authenticatedUser,
        parent.name,
        client,
      );
    },
  },
};
