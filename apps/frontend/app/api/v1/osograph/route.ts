import { ApolloServer } from "@apollo/server";
import { startServerAndCreateNextHandler } from "@as-integrations/next";
import { NextRequest, NextResponse } from "next/server";
import { readFileSync } from "fs";
import path from "path";
import { gql } from "graphql-tag";
import { getUser } from "@/lib/auth/auth";
import { buildSubgraphSchema } from "@apollo/subgraph";
import { resolvers } from "@/app/api/v1/osograph/schema/resolvers";

function loadSchemas(): string {
  const schemaDir = path.join(
    process.cwd(),
    "./app/api/v1/osograph/schema/graphql",
  );

  const schemaFiles = [
    "base.graphql",
    "user.graphql",
    "organization.graphql",
    "invitation.graphql",
    "notebook.graphql",
    "dataset.graphql",
  ];

  const schemas = schemaFiles.map((file) => {
    const filePath = path.join(schemaDir, file);
    return readFileSync(filePath, "utf-8");
  });

  return schemas.join("\n\n");
}

const schemaString = loadSchemas();
const typeDefs = gql(schemaString);

const server = new ApolloServer({
  schema: buildSubgraphSchema([{ typeDefs, resolvers }]),
  introspection: true,
  includeStacktraceInErrorResponses: process.env.NODE_ENV === "development",
});

const apolloHandler = startServerAndCreateNextHandler<NextRequest>(server, {
  context: async (req) => {
    const user = await getUser(req);
    return { req, user };
  },
});

const handler = async (req: NextRequest) => {
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
