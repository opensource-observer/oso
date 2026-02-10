import { ApolloServer } from "@apollo/server";
import { startServerAndCreateNextHandler } from "@as-integrations/next";
import { NextRequest, NextResponse } from "next/server";
import { readdirSync, readFileSync } from "fs";
import path from "path";
import { gql } from "graphql-tag";
import { getSystemCredentials, getUser } from "@/lib/auth/auth";
import { buildSubgraphSchema } from "@apollo/subgraph";
import { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { shouldUseNewResolvers } from "@/lib/feature-flags/posthog-features";
import { resolvers as newResolvers } from "@/app/api/v1/osograph/schema/resolvers";
import { resolvers as oldResolvers } from "@/app/api/v1/osograph/schema/resolvers/legacy";

function loadSchemas(): string {
  const schemaDir = path.join(
    process.cwd(),
    "./app/api/v1/osograph/schema/graphql",
  );

  const baseSchema = readFileSync(
    path.join(schemaDir, "base.graphql"),
    "utf-8",
  );

  const otherSchemaFiles = readdirSync(schemaDir)
    .filter((file) => file.endsWith(".graphql") && file !== "base.graphql")
    .sort();

  const otherSchemas = otherSchemaFiles.map((file) => {
    const filePath = path.join(schemaDir, file);
    return readFileSync(filePath, "utf-8");
  });

  return [baseSchema, ...otherSchemas].join("\n\n");
}

const schemaString = loadSchemas();
const typeDefs = gql(schemaString);

const newResolverServer = new ApolloServer({
  schema: buildSubgraphSchema([{ typeDefs, resolvers: newResolvers }]),
  introspection: true,
  includeStacktraceInErrorResponses: process.env.NODE_ENV === "development",
});

const oldResolverServer = new ApolloServer({
  schema: buildSubgraphSchema([{ typeDefs, resolvers: oldResolvers }]),
  introspection: true,
  includeStacktraceInErrorResponses: process.env.NODE_ENV === "development",
});

const newResolverHandler = startServerAndCreateNextHandler<NextRequest>(
  newResolverServer,
  {
    context: async (req) => {
      const user = await getUser(req);
      const systemCredentials = await getSystemCredentials(req);
      return {
        req,
        user,
        systemCredentials,
        authCache: {
          orgMemberships: new Map(),
          resourcePermissions: new Map(),
        },
      } satisfies GraphQLContext;
    },
  },
);

const oldResolverHandler = startServerAndCreateNextHandler<NextRequest>(
  oldResolverServer,
  {
    context: async (req) => {
      const user = await getUser(req);
      const systemCredentials = await getSystemCredentials(req);
      return {
        req,
        user,
        systemCredentials,
        authCache: {
          orgMemberships: new Map(),
          resourcePermissions: new Map(),
        },
      } satisfies GraphQLContext;
    },
  },
);

const handler = async (req: NextRequest) => {
  const user = await getUser(req);
  const useNewResolvers = await shouldUseNewResolvers(user);

  const apolloHandler = useNewResolvers
    ? newResolverHandler
    : oldResolverHandler;

  return apolloHandler(req);
};

export function OPTIONS() {
  return new NextResponse(null, {
    status: 204,
    headers: {
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization",
    },
  });
}

export { handler as GET, handler as POST };
