import { getOrgResourceClient } from "@/app/api/v1/osograph/utils/access-control";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { getOrganization } from "@/app/api/v1/osograph/utils/auth";
import { ResourceErrors } from "@/app/api/v1/osograph/utils/errors";
import {
  getMaterializations,
  getModelRunConnection,
  getResourceById,
} from "@/app/api/v1/osograph/utils/resolver-helpers";
import {
  ConnectionArgs,
  FilterableConnectionArgs,
} from "@/app/api/v1/osograph/utils/pagination";
import {
  DataModelReleaseWhereSchema,
  DataModelRevisionWhereSchema,
} from "@/app/api/v1/osograph/utils/validation";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import { queryWithPagination } from "@/app/api/v1/osograph/utils/query-helpers";
import {
  ModelRow,
  ModelRevisionRow,
  ModelReleaseRow,
} from "@/lib/types/schema-types";
import { getModelContext } from "@/app/api/v1/osograph/schema/resolvers/model-context";
import { generateTableId } from "@/app/api/v1/osograph/utils/model";

/**
 * Type resolvers for DataModel, DataModelRevision, and DataModelRelease.
 * These field resolvers don't require auth checks as they operate on
 * already-fetched data model data.
 */
export const dataModelTypeResolvers: GraphQLResolverModule<GraphQLContext> = {
  DataModel: {
    orgId: (parent: ModelRow) => parent.org_id,
    organization: async (
      parent: ModelRow,
      _args: unknown,
      context: GraphQLContext,
    ) => {
      const { client } = await getOrgResourceClient(
        context,
        "data_model",
        parent.id,
      );
      return getOrganization(parent.org_id, client);
    },
    dataset: async (
      parent: ModelRow,
      _args: unknown,
      context: GraphQLContext,
    ) => {
      const { client } = await getOrgResourceClient(
        context,
        "data_model",
        parent.id,
      );
      return getResourceById(
        {
          tableName: "datasets",
          id: parent.dataset_id,
          userId: "",
        },
        client,
      );
    },
    revisions: async (
      parent: ModelRow,
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      const { client } = await getOrgResourceClient(
        context,
        "data_model",
        parent.id,
        "read",
      );

      return queryWithPagination(args, context, {
        client,
        orgIds: parent.org_id,
        tableName: "model_revision",
        whereSchema: DataModelRevisionWhereSchema,
        basePredicate: {
          eq: [{ key: "model_id", value: parent.id }],
        },
      });
    },
    releases: async (
      parent: ModelRow,
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      const { client } = await getOrgResourceClient(
        context,
        "data_model",
        parent.id,
        "read",
      );

      return queryWithPagination(args, context, {
        client,
        orgIds: parent.org_id,
        tableName: "model_release",
        whereSchema: DataModelReleaseWhereSchema,
        basePredicate: {
          eq: [{ key: "model_id", value: parent.id }],
        },
        orderBy: {
          key: "created_at",
          ascending: false,
        },
      });
    },
    isEnabled: (parent: ModelRow) => parent.is_enabled,
    createdAt: (parent: ModelRow) => parent.created_at,
    updatedAt: (parent: ModelRow) => parent.updated_at,
    latestRevision: async (
      parent: ModelRow,
      _args: unknown,
      context: GraphQLContext,
    ) => {
      const { client } = await getOrgResourceClient(
        context,
        "data_model",
        parent.id,
      );
      const { data, error } = await client
        .from("model_revision")
        .select("*")
        .eq("model_id", parent.id)
        .order("revision_number", { ascending: false })
        .limit(1)
        .single();

      if (error) {
        return null;
      }
      return data;
    },
    latestRelease: async (
      parent: ModelRow,
      _args: unknown,
      context: GraphQLContext,
    ) => {
      const { client } = await getOrgResourceClient(
        context,
        "data_model",
        parent.id,
      );
      const { data, error } = await client
        .from("model_release")
        .select("*")
        .eq("model_id", parent.id)
        .order("created_at", { ascending: false })
        .limit(1)
        .single();

      if (error) {
        return null;
      }
      return data;
    },

    runs: async (
      parent: ModelRow,
      args: ConnectionArgs,
      context: GraphQLContext,
    ) => {
      const { client } = await getOrgResourceClient(
        context,
        "data_model",
        parent.id,
      );
      return getModelRunConnection(parent.dataset_id, parent.id, args, client);
    },
    modelContext: async (parent: ModelRow) => {
      return getModelContext(parent.dataset_id, parent.id);
    },
    materializations: async (
      parent: ModelRow,
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      return getMaterializations(
        args,
        context,
        parent.org_id,
        parent.dataset_id,
        generateTableId("USER_MODEL", parent.id),
      );
    },
  },

  DataModelRevision: {
    orgId: (parent: ModelRevisionRow) => parent.org_id,
    dataModelId: (parent: ModelRevisionRow) => parent.model_id,
    dataModel: async (
      parent: ModelRevisionRow,
      _args: unknown,
      context: GraphQLContext,
    ) => {
      const { client } = await getOrgResourceClient(
        context,
        "data_model",
        parent.model_id,
      );
      const { data, error } = await client
        .from("model")
        .select("*")
        .eq("id", parent.model_id)
        .single();
      if (error) {
        throw ResourceErrors.notFound("DataModel", parent.model_id);
      }
      return data;
    },
    organization: async (
      parent: ModelRevisionRow,
      _args: unknown,
      context: GraphQLContext,
    ) => {
      const { client } = await getOrgResourceClient(
        context,
        "data_model",
        parent.model_id,
      );
      return getOrganization(parent.org_id, client);
    },
    revisionNumber: (parent: ModelRevisionRow) => parent.revision_number,
    start: (parent: ModelRevisionRow) => parent.start,
    end: (parent: ModelRevisionRow) => parent.end,
    dependsOn: (parent: ModelRevisionRow) => parent.depends_on,
    partitionedBy: (parent: ModelRevisionRow) => parent.partitioned_by,
    clusteredBy: (parent: ModelRevisionRow) => parent.clustered_by,
    kindOptions: (parent: ModelRevisionRow) => parent.kind_options,
    createdAt: (parent: ModelRevisionRow) => parent.created_at,
  },

  DataModelRelease: {
    orgId: (parent: ModelReleaseRow) => parent.org_id,
    dataModelId: (parent: ModelReleaseRow) => parent.model_id,
    revisionId: (parent: ModelReleaseRow) => parent.model_revision_id,
    dataModel: async (
      parent: ModelReleaseRow,
      _args: unknown,
      context: GraphQLContext,
    ) => {
      const { client } = await getOrgResourceClient(
        context,
        "data_model",
        parent.model_id,
      );
      const { data, error } = await client
        .from("model")
        .select("*")
        .eq("id", parent.model_id)
        .single();
      if (error) {
        throw ResourceErrors.notFound("DataModel", parent.model_id);
      }
      return data;
    },
    revision: async (
      parent: ModelReleaseRow,
      _args: unknown,
      context: GraphQLContext,
    ) => {
      const { client } = await getOrgResourceClient(
        context,
        "data_model",
        parent.model_id,
      );
      const { data, error } = await client
        .from("model_revision")
        .select("*")
        .eq("id", parent.model_revision_id)
        .single();
      if (error) {
        throw ResourceErrors.notFound(
          "DataModelRevision",
          parent.model_revision_id,
        );
      }
      return data;
    },
    organization: async (
      parent: ModelReleaseRow,
      _args: unknown,
      context: GraphQLContext,
    ) => {
      const { client } = await getOrgResourceClient(
        context,
        "data_model",
        parent.model_id,
      );
      return getOrganization(parent.org_id, client);
    },
    createdAt: (parent: ModelReleaseRow) => parent.created_at,
    updatedAt: (parent: ModelReleaseRow) => parent.updated_at,
  },
};
