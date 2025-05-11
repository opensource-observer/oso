import { ApolloServer } from "@apollo/server";
import { ApolloGateway, RemoteGraphQLDataSource } from "@apollo/gateway";
import { startServerAndCreateNextHandler } from "@as-integrations/next";
import { readFileSync } from "fs";
import path from "path";
import { NextRequest } from "next/server";
//import { ApolloGateway, IntrospectAndCompose } from "@apollo/gateway";
//import { HASURA_URL } from "../../../../lib/config";

// https://vercel.com/guides/loading-static-file-nextjs-api-route
const supergraphPath = path.join(
  process.cwd(),
  "./app/api/v1/graphql/supergraph.graphql",
);
const supergraphSdl = readFileSync(supergraphPath).toString();

// Setup the Apollo Gateway and server
const gateway = new ApolloGateway({
  supergraphSdl,
  buildService({ url }) {
    return new RemoteGraphQLDataSource({ url });
  },
  /**
  supergraphSdl: new IntrospectAndCompose({
    subgraphs: [
      { name: "hasura", url: HASURA_URL },
      //{ name: 'products', url: 'http://localhost:4002' },
    ],
  }),
  */
});

const server = new ApolloServer({
  gateway,
  introspection: true,
});

const handler = startServerAndCreateNextHandler<NextRequest>(server, {
  // Use this to add custom middleware to set context
  context: async (req) => {
    const userId = req.headers.get("x-user-id");
    const userRole = req.headers.get("x-user-role");
    const keyName = req.headers.get("x-user-key-name");

    const user = {
      userId: userId || "",
      role: userRole || "anonymous",
      keyName: keyName || "",
    };

    return { req, user };
  },
});

export { handler as GET, handler as POST };
