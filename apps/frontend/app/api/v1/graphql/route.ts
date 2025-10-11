import { ApolloServer } from "@apollo/server";
import {
  ApolloGateway,
  GraphQLDataSourceProcessOptions,
  RemoteGraphQLDataSource,
} from "@apollo/gateway";
import { startServerAndCreateNextHandler } from "@as-integrations/next";
import { OperationDefinitionNode, parse } from "graphql";
import { readFileSync } from "fs";
import path from "path";
import { NextRequest, NextResponse } from "next/server";
import { EVENTS } from "@/lib/types/posthog";
import { getOrgUser } from "@/lib/auth/auth";
import { trackServerEvent } from "@/lib/analytics/track";
import { logger } from "@/lib/logger";
import {
  CreditsService,
  TransactionType,
  InsufficientCreditsError,
} from "@/lib/services/credits";
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
 * Check if a GraphQL query is purely an introspection query
 *
 * Per the GraphQL spec, introspection fields are prefixed with "__" (two underscores):
 * "Types and fields required by the GraphQL introspection system that are used in
 * the same context as user defined types and fields are prefixed with "__" (two
 * underscores), in order to avoid naming collisions with user defined GraphQL types."
 *
 * @see https://github.com/graphql/graphql-spec/blob/main/spec/Section%204%20--%20Introspection.md#reserved-names
 * @param queryString
 * @returns true if query only contains introspection fields (starting with __)
 */
function isIntrospectionQuery(queryString: string): boolean {
  try {
    const document = parse(queryString);

    for (const def of document.definitions) {
      // Per GraphQL spec, ExecutableDefinition consists of OperationDefinition | FragmentDefinition
      // We only check OperationDefinitions since introspection queries are operations
      // @see https://github.com/graphql/graphql-spec/blob/main/spec/Section%202%20--%20Language.md#document
      if (def.kind !== "OperationDefinition") continue;

      for (const selection of def.selectionSet.selections) {
        if (
          selection.kind === "Field" &&
          !selection.name.value.startsWith("__")
        ) {
          return false;
        }
      }
    }

    return true;
  } catch {
    return false;
  }
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

  const user = await getOrgUser(req);
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

  const isIntrospection = isIntrospectionQuery(query);

  if (isIntrospection) {
    const apolloHandler = startServerAndCreateNextHandler<NextRequest>(server, {
      context: async () => ({ req, user }),
    });
    return apolloHandler(req);
  }

  if (user.role === "anonymous") {
    logger.log(`/api/graphql: User is anonymous`);
    return NextResponse.json(
      { error: "Authentication required" },
      { status: 401 },
    );
  }

  try {
    await CreditsService.checkAndDeductOrganizationCredits(
      user,
      user.orgId,
      TransactionType.GRAPHQL_QUERY,
      tracker,
      "/api/v1/graphql",
      { operation, query },
    );
  } catch (error) {
    if (error instanceof InsufficientCreditsError) {
      return NextResponse.json({ error: error.message }, { status: 402 });
    }
    logger.error(
      `/api/graphql: Error tracking usage for user ${user.userId}:`,
      error,
    );
  }

  const apolloHandler = startServerAndCreateNextHandler<NextRequest>(server, {
    context: async () => ({ req, user }),
  });

  return apolloHandler(req);
};

const wrappedHandler = withPostHogTracking(customHandler);

export { wrappedHandler as GET, wrappedHandler as POST };
