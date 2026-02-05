import { DateTimeISOResolver, GraphQLJSON } from "graphql-scalars";
import type { GraphQLResolverMap } from "@apollo/subgraph/dist/schema-helper/resolverMap";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";

import { systemResolvers } from "@/app/api/v1/osograph/schema/resolvers/system/index";
import { organizationResolvers } from "@/app/api/v1/osograph/schema/resolvers/organization/index";
import { resourceResolvers } from "@/app/api/v1/osograph/schema/resolvers/resource/index";
import { userResolvers } from "@/app/api/v1/osograph/schema/resolvers/user/index";

export const resolvers: GraphQLResolverMap<GraphQLContext> = {
  DateTime: DateTimeISOResolver,
  JSON: GraphQLJSON,

  Query: {
    ...userResolvers.Query,
    ...organizationResolvers.Query,
    ...resourceResolvers.Query,
    ...systemResolvers.Query,
  },

  Mutation: {
    ...userResolvers.Mutation,
    ...organizationResolvers.Mutation,
    ...resourceResolvers.Mutation,
    ...systemResolvers.Mutation,
  },

  Viewer: userResolvers.Viewer,
  User: userResolvers.User,
  Organization: organizationResolvers.Organization,
  OrganizationMember: organizationResolvers.OrganizationMember,
  Invitation: userResolvers.Invitation,

  Notebook: resourceResolvers.Notebook,
  Dataset: resourceResolvers.Dataset,
  DataModelDefinition: resourceResolvers.DataModelDefinition,
  StaticModelDefinition: resourceResolvers.StaticModelDefinition,
  DataIngestionDefinition: resourceResolvers.DataIngestionDefinition,
  DataIngestion: resourceResolvers.DataIngestion,
  DataModel: resourceResolvers.DataModel,
  DataModelRevision: resourceResolvers.DataModelRevision,
  DataModelRelease: resourceResolvers.DataModelRelease,
  StaticModel: resourceResolvers.StaticModel,
  DataConnection: resourceResolvers.DataConnection,
  DataConnectionAlias: resourceResolvers.DataConnectionAlias,
  ModelContext: resourceResolvers.ModelContext,

  Run: systemResolvers.Run,
  Step: systemResolvers.Step,
  Materialization: systemResolvers.Materialization,
  System: systemResolvers.System,
};
