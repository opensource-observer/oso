import { ApolloServer } from "@apollo/server";
import { buildSubgraphSchema } from "@apollo/subgraph";
import { startServerAndCreateNextHandler } from "@as-integrations/next";
import { NextRequest, NextResponse } from "next/server";
import { readFileSync } from "fs";
import path from "path";
import { gql } from "graphql-tag";
import { getOrgUser } from "@/lib/auth/auth";
import { resolvers } from "@/app/api/v1/osograph/schema/resolvers";

const schemaPath = path.join(
  process.cwd(),
  "./app/api/v1/osograph/schema.graphql",
);
const schemaString = readFileSync(schemaPath, "utf-8");
const typeDefs = gql(schemaString);

const server = new ApolloServer({
  schema: buildSubgraphSchema([{ typeDefs, resolvers }]),
  introspection: true,
  includeStacktraceInErrorResponses: false,
});

const apolloHandler = startServerAndCreateNextHandler<NextRequest>(server, {
  context: async (req) => {
    const user = await getOrgUser(req);
    return { req, user };
  },
});

const handler = async (req: NextRequest) => {
  return apolloHandler(req);
};

export function OPTIONS() {
  return new NextResponse(null, { status: 204 });
}

export { handler as GET, handler as POST };
