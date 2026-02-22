import { ApolloServer } from "@apollo/server";
import { startServerAndCreateNextHandler } from "@as-integrations/next";
import { NextRequest, NextResponse } from "next/server";
import { readdirSync, readFileSync } from "fs";
import path from "path";
import { gql } from "graphql-tag";
import { getSystemCredentials, getUser } from "@/lib/auth/auth";
import { buildSubgraphSchema } from "@apollo/subgraph";
import { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { resolvers } from "@/app/api/v1/osograph/schema/resolvers";
import { withPostHogTracking } from "@/lib/clients/posthog";

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

const server = new ApolloServer({
  schema: buildSubgraphSchema([{ typeDefs, resolvers }]),
  introspection: true,
  includeStacktraceInErrorResponses: process.env.NODE_ENV === "development",
});

const handler = startServerAndCreateNextHandler<NextRequest>(server, {
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
        orgIds: new Map(),
      },
    } satisfies GraphQLContext;
  },
});

export function OPTIONS() {
  return new NextResponse(null, {
    status: 204,
    headers: {
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization",
    },
  });
}

const wrappedHandler = withPostHogTracking(handler);

export { wrappedHandler as GET, wrappedHandler as POST };
