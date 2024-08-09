import { ApolloServer } from "@apollo/server";
import { ApolloGateway, IntrospectAndCompose } from "@apollo/gateway";
import { startServerAndCreateNextHandler } from "@as-integrations/next";
import { NextRequest } from "next/server";
import { HASURA_URL } from "../../../../lib/config";

const gateway = new ApolloGateway({
  supergraphSdl: new IntrospectAndCompose({
    subgraphs: [
      { name: "hasura", url: HASURA_URL },
      //{ name: 'products', url: 'http://localhost:4002' },
    ],
  }),
});

const server = new ApolloServer({
  gateway,
  introspection: true,
});

const handler = startServerAndCreateNextHandler<NextRequest>(server, {
  context: async (req) => ({ req }),
});

export { handler as GET, handler as POST };
