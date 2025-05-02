import { ApolloServer } from "@apollo/server";
import {
  ApolloGateway,
  RemoteGraphQLDataSource,
  GraphQLDataSourceProcessOptions,
} from "@apollo/gateway";
import { startServerAndCreateNextHandler } from "@as-integrations/next";
import { OperationDefinitionNode } from "graphql";
import { readFileSync } from "fs";
import path from "path";
import { NextRequest } from "next/server";
import { spawn } from "@opensource-observer/utils";
import { withPostHog } from "../../../../lib/clients/posthog";
import { EVENTS } from "../../../../lib/types/posthog";
import { AuthUser } from "../../../../lib/auth/auth";
//import { ApolloGateway, IntrospectAndCompose } from "@apollo/gateway";
//import { HASURA_URL } from "../../../../lib/config";

// https://vercel.com/guides/loading-static-file-nextjs-api-route
const supergraphPath = path.join(
  process.cwd(),
  "./app/api/v1/graphql/supergraph.graphql",
);
const supergraphSdl = readFileSync(supergraphPath).toString();

/**
 * Extract all model names from a GraphQL operation
 * @param operation
 * @returns
 */
function getModelNames(operation: OperationDefinitionNode): string[] {
  const modelNames: string[] = [];
  const selectionSet = operation.selectionSet.selections;

  for (const selection of selectionSet) {
    if (selection.kind === "Field") {
      const fieldName = selection.name.value;
      modelNames.push(fieldName);
    }
  }

  return modelNames;
}

/**
 * Custom Apollo Gateway Data Source,
 * used to inspect the GraphQL operation in-line
 */
class AuthenticatedDataSource extends RemoteGraphQLDataSource {
  willSendRequest(opts: GraphQLDataSourceProcessOptions) {
    if (opts.kind !== "incoming operation") {
      return;
    }
    const op = opts.incomingRequestContext.operation;
    const modelNames = getModelNames(op);
    //console.log(modelNames);
    spawn(
      withPostHog(async (posthog, user: AuthUser) => {
        posthog.capture({
          distinctId: user.userId,
          event: EVENTS.API_CALL,
          properties: {
            type: "graphql",
            operation: op.operation,
            models: modelNames,
            query: opts.request.query,
            apiKeyName: user.keyName,
          },
        });
      }, opts.context.req),
    );
  }
}

// Setup the Apollo Gateway and server
const gateway = new ApolloGateway({
  supergraphSdl,
  buildService({ url }) {
    return new AuthenticatedDataSource({ url });
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
    //const user = await getUser(req);
    return { req };
  },
});

export { handler as GET, handler as POST };
