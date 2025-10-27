import { GraphQLScalarType, Kind } from "graphql";
import type { GraphQLResolverMap } from "@apollo/subgraph/dist/schema-helper/resolverMap";
import type { GraphQLContext } from "@/app/api/v1/osograph/utils/auth";
import { organizationResolvers } from "@/app/api/v1/osograph/schema/resolvers/organization";
import { userResolvers } from "@/app/api/v1/osograph/schema/resolvers/user";
import { memberResolvers } from "@/app/api/v1/osograph/schema/resolvers/member";
import { invitationResolvers } from "@/app/api/v1/osograph/schema/resolvers/invitation";
import { catalogResolvers } from "@/app/api/v1/osograph/schema/resolvers/catalog";

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
    ...userResolvers.Query,
    ...organizationResolvers.Query,
    ...invitationResolvers.Query,
    ...catalogResolvers.Query,
  },
  Mutation: {
    ...userResolvers.Mutation,
    ...memberResolvers.Mutation,
    ...invitationResolvers.Mutation,
  },
  User: userResolvers.User,
  Organization: organizationResolvers.Organization,
  OrganizationMember: memberResolvers.OrganizationMember,
  Invitation: invitationResolvers.Invitation,
};
