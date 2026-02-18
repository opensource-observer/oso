import type { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { notebookResolvers } from "@/app/api/v1/osograph/schema/resolvers/resource/notebook";
import { datasetResolvers } from "@/app/api/v1/osograph/schema/resolvers/resource/dataset";
import { dataModelResolvers } from "@/app/api/v1/osograph/schema/resolvers/resource/data-model";
import { staticModelResolvers } from "@/app/api/v1/osograph/schema/resolvers/resource/static-model";
import { dataIngestionResolvers } from "@/app/api/v1/osograph/schema/resolvers/resource/data-ingestion";
import { dataConnectionResolvers } from "@/app/api/v1/osograph/schema/resolvers/resource/data-connection";
import { modelContextResolvers } from "@/app/api/v1/osograph/schema/resolvers/resource/model-context";
import { resourceMutations } from "@/app/api/v1/osograph/schema/resolvers/resource/mutations";

/**
 * Resource-scoped resolvers.
 * These resolvers use getOrgResourceClient for fine-grained permission checks
 * on specific resources (notebooks, datasets, models, etc.).
 */
export const resourceResolvers: GraphQLResolverModule<GraphQLContext> = {
  Query: {
    ...notebookResolvers.Query,
    ...datasetResolvers.Query,
    ...dataModelResolvers.Query,
    ...staticModelResolvers.Query,
    ...dataConnectionResolvers.Query,
  },
  Mutation: {
    ...resourceMutations,
    ...notebookResolvers.Mutation,
    ...datasetResolvers.Mutation,
    ...dataModelResolvers.Mutation,
    ...staticModelResolvers.Mutation,
    ...dataIngestionResolvers.Mutation,
    ...dataConnectionResolvers.Mutation,
    ...modelContextResolvers.Mutation,
  },
  Notebook: notebookResolvers.Notebook,
  Dataset: datasetResolvers.Dataset,
  DataModelDefinition: datasetResolvers.DataModelDefinition,
  StaticModelDefinition: datasetResolvers.StaticModelDefinition,
  DataIngestionDefinition: datasetResolvers.DataIngestionDefinition,
  DataConnectionDefinition: datasetResolvers.DataConnectionDefinition,
  DataModel: dataModelResolvers.DataModel,
  DataModelRevision: dataModelResolvers.DataModelRevision,
  DataModelRelease: dataModelResolvers.DataModelRelease,
  StaticModel: staticModelResolvers.StaticModel,
  DataIngestion: dataIngestionResolvers.DataIngestion,
  DataConnection: dataConnectionResolvers.DataConnection,
  DataConnectionAlias: dataConnectionResolvers.DataConnectionAlias,
  ModelContext: modelContextResolvers.ModelContext,
};
