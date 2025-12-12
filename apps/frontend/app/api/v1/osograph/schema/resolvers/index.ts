import { DateTimeISOResolver, GraphQLJSON } from "graphql-scalars";
import type { GraphQLResolverMap } from "@apollo/subgraph/dist/schema-helper/resolverMap";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { viewerResolvers } from "@/app/api/v1/osograph/schema/resolvers/viewer";
import { userResolvers } from "@/app/api/v1/osograph/schema/resolvers/user";
import { organizationResolvers } from "@/app/api/v1/osograph/schema/resolvers/organization";
import { invitationResolvers } from "@/app/api/v1/osograph/schema/resolvers/invitation";
import { notebookResolvers } from "@/app/api/v1/osograph/schema/resolvers/notebook";
import { datasetResolvers } from "@/app/api/v1/osograph/schema/resolvers/dataset";
import { dataModelResolvers } from "@/app/api/v1/osograph/schema/resolvers/data-model";
import { schedulerResolvers } from "@/app/api/v1/osograph/schema/resolvers/scheduler";
import { systemResolvers } from "@/app/api/v1/osograph/schema/resolvers/system";
import { staticModelResolvers } from "@/app/api/v1/osograph/schema/resolvers/static-model";

export const resolvers: GraphQLResolverMap<GraphQLContext> = {
  DateTime: DateTimeISOResolver,
  JSON: GraphQLJSON,

  Query: {
    ...viewerResolvers.Query,
    ...organizationResolvers.Query,
    ...invitationResolvers.Query,
    ...notebookResolvers.Query,
    ...datasetResolvers.Query,
    ...dataModelResolvers.Query,
    ...staticModelResolvers.Query,
    ...systemResolvers.Query,
  },

  Mutation: {
    ...organizationResolvers.Mutation,
    ...invitationResolvers.Mutation,
    ...notebookResolvers.Mutation,
    ...datasetResolvers.Mutation,
    ...dataModelResolvers.Mutation,
    ...staticModelResolvers.Mutation,
    ...schedulerResolvers.Mutation,
    ...systemResolvers.Mutation,
  },

  Viewer: viewerResolvers.Viewer,
  User: userResolvers.User,
  Organization: organizationResolvers.Organization,
  OrganizationMember: organizationResolvers.OrganizationMember,
  Invitation: invitationResolvers.Invitation,
  Notebook: notebookResolvers.Notebook,
  Dataset: datasetResolvers.Dataset,
  DataModelDefinition: datasetResolvers.DataModelDefinition,
  StaticModelDefinition: datasetResolvers.StaticModelDefinition,
  DataModel: dataModelResolvers.DataModel,
  DataModelRevision: dataModelResolvers.DataModelRevision,
  DataModelRelease: dataModelResolvers.DataModelRelease,
  StaticModel: staticModelResolvers.StaticModel,
  Run: schedulerResolvers.Run,
  Materialization: schedulerResolvers.Materialization,
  System: systemResolvers.System,
};
