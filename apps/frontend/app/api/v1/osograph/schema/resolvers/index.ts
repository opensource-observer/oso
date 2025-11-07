import { GraphQLScalarType, Kind } from "graphql";
import type { GraphQLResolverMap } from "@apollo/subgraph/dist/schema-helper/resolverMap";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { viewerResolvers } from "@/app/api/v1/osograph/schema/resolvers/viewer";
import { userResolvers } from "@/app/api/v1/osograph/schema/resolvers/user";
import { organizationResolvers } from "@/app/api/v1/osograph/schema/resolvers/organization";
import { invitationResolvers } from "@/app/api/v1/osograph/schema/resolvers/invitation";
import { notebookResolvers } from "@/app/api/v1/osograph/schema/resolvers/notebook";
import { datasetResolvers } from "@/app/api/v1/osograph/schema/resolvers/dataset";

const dateTimeScalar = new GraphQLScalarType({
  name: "DateTime",
  description: "DateTime custom scalar type",
  serialize(value) {
    if (value instanceof Date) {
      return value.toISOString();
    }
    if (typeof value === "string") {
      return value;
    }
    throw Error("DateTime must be a Date object or ISO string");
  },
  parseValue(value) {
    if (typeof value === "string") {
      return new Date(value);
    }
    throw Error("DateTime must be a string");
  },
  parseLiteral(ast) {
    if (ast.kind === Kind.STRING) {
      return new Date(ast.value);
    }
    return null;
  },
});

export const resolvers: GraphQLResolverMap<GraphQLContext> = {
  DateTime: dateTimeScalar,

  Query: {
    ...viewerResolvers.Query,
    ...organizationResolvers.Query,
    ...invitationResolvers.Query,
    ...notebookResolvers.Query,
    ...datasetResolvers.Query,
  },

  Mutation: {
    ...organizationResolvers.Mutation,
    ...invitationResolvers.Mutation,
    ...notebookResolvers.Mutation,
    ...datasetResolvers.Mutation,
  },

  Viewer: viewerResolvers.Viewer,
  User: userResolvers.User,
  Organization: organizationResolvers.Organization,
  OrganizationMember: organizationResolvers.OrganizationMember,
  Invitation: invitationResolvers.Invitation,
  Notebook: notebookResolvers.Notebook,
  Dataset: datasetResolvers.Dataset,
};
