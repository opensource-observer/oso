import { ApolloServer } from "@apollo/server";
import {
  ApolloGateway,
  GraphQLDataSourceProcessOptions,
  RemoteGraphQLDataSource,
} from "@apollo/gateway";
import { startServerAndCreateNextHandler } from "@as-integrations/next";
import { OperationDefinitionNode } from "graphql";
import { readFileSync } from "fs";
import path from "path";
import { NextRequest, NextResponse } from "next/server";
import { EVENTS } from "@/lib/types/posthog";
import { getUser } from "@/lib/auth/auth";
import { trackServerEvent } from "@/lib/analytics/track";
import { logger } from "@/lib/logger";
import { CreditsService, TransactionType } from "@/lib/services/credits";
import { withPostHogTracking } from "@/lib/clients/posthog";

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
  async willSendRequest(opts: GraphQLDataSourceProcessOptions) {
    if (opts.kind !== "incoming operation") {
      return;
    }
    const op = opts.incomingRequestContext.operation;
    const modelNames = getModelNames(op);
    const user = opts.context.user;
    const tracker = trackServerEvent(user);

    if (user && user.role !== "anonymous") {
      tracker.track(EVENTS.API_CALL, {
        type: "graphql",
        operation: op.operation,
        models: modelNames,
        query: opts.request.query,
      });
    } else {
      logger.warn("/graphql: User is anonymous. No tracking");
    }
  }
}

// Setup the Apollo Gateway and server
const gateway = new ApolloGateway({
  supergraphSdl,
  buildService({ url }) {
    return new AuthenticatedDataSource({ url });
  },
});

const server = new ApolloServer({
  gateway,
  introspection: true,
});

const customHandler = async (req: NextRequest) => {
  if (req.method === "OPTIONS") {
    return new NextResponse(null, { status: 204 });
  }

  const user = await getUser(req);
  const requestClone = req.clone();
  const tracker = trackServerEvent(user);

  let operation = "unknown";
  let query = "";

  try {
    const body = await requestClone.json();
    query = body.query || "";

    // TODO(jabolo): Use a real parser to extract operation type and name
    if (query.includes("query")) {
      operation = "query";
    } else if (query.includes("mutation")) {
      operation = "mutation";
    } else if (query.includes("subscription")) {
      operation = "subscription";
    }
  } catch (error) {
    logger.error("Error parsing GraphQL request body:", error);
  }

  if (user.role !== "anonymous") {
    const orgId = user.orgId;

    if (orgId) {
      try {
        await CreditsService.checkAndDeductOrganizationCredits(
          user,
          orgId,
          TransactionType.GRAPHQL_QUERY,
          tracker,
          "/api/v1/graphql",
          { operation, query },
        );
      } catch (error) {
        logger.error(
          `/api/graphql: Error tracking usage for user ${user.userId}:`,
          error,
        );
      }
    }
  }

  const apolloHandler = startServerAndCreateNextHandler<NextRequest>(server, {
    context: async () => {
      return { req, user };
    },
  });

  return apolloHandler(req);
};

const wrappedHandler = withPostHogTracking(customHandler);

export { wrappedHandler as GET, wrappedHandler as POST };
