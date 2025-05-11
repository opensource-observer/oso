import { type NextRequest, NextResponse } from "next/server";
import { getUser } from "./lib/auth/auth";
import { EVENTS } from "./lib/types/posthog";
import { logger } from "./lib/logger";
import { getTableNamesFromSql } from "./lib/parsing";
import type { User } from "./lib/types/user";
import { OperationDefinitionNode, parse, visit } from "graphql";
import { POSTHOG_HOST_DIRECT, POSTHOG_KEY } from "./lib/config";

const API_TYPES = ["sql", "graphql", "chat"] as const;
type ApiType = (typeof API_TYPES)[number];

interface SqlRequestBody {
  query: string;
  format?: string;
}

interface GraphQLRequestBody {
  query: string;
  variables?: Record<string, unknown>;
  operationName?: string;
}

interface ChatMessage {
  role: string;
  content: string;
}

interface ChatRequestBody {
  messages: ChatMessage[];
}

type ApiRequestBody = SqlRequestBody | GraphQLRequestBody | ChatRequestBody;

function isSqlBody(body: unknown): body is SqlRequestBody {
  return typeof body === "object" && body !== null && "query" in body;
}

function isGraphQLBody(body: unknown): body is GraphQLRequestBody {
  return typeof body === "object" && body !== null && "query" in body;
}

function isChatBody(body: unknown): body is ChatRequestBody {
  return (
    typeof body === "object" &&
    body !== null &&
    "messages" in body &&
    Array.isArray((body as ChatRequestBody).messages)
  );
}

interface BaseTrackingData {
  type: ApiType;
  endpoint: string;
  method: string;
  userId: string;
  apiKeyName: string;
  host: string | null;
}

interface SqlTrackingData extends BaseTrackingData {
  type: "sql";
  query: string;
  models: string[];
}

interface GraphQLTrackingData extends BaseTrackingData {
  type: "graphql";
  query: string;
  operation?: string;
  models?: string[];
  operationName?: string;
}

interface ChatTrackingData extends BaseTrackingData {
  type: "chat";
  message: string;
}

type TrackingData = SqlTrackingData | GraphQLTrackingData | ChatTrackingData;

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

function parseGraphQLQuery(query: string): {
  operation?: string;
  models?: string[];
} {
  try {
    const document = parse(query);
    let operation: string | undefined;
    let models: string[] | undefined;

    visit(document, {
      OperationDefinition(node) {
        operation = node.operation;
        models = getModelNames(node);
      },
    });

    return { operation, models };
  } catch (error) {
    logger.warn("Failed to parse GraphQL query", error);
    return {};
  }
}

type TrackCallback<T extends ApiRequestBody, R> = (body: T) => R;

const TRACK_CALLBACKS: {
  sql: TrackCallback<SqlRequestBody, Pick<SqlTrackingData, "query" | "models">>;
  graphql: TrackCallback<
    GraphQLRequestBody,
    Pick<
      GraphQLTrackingData,
      "query" | "operation" | "models" | "operationName"
    >
  >;
  chat: TrackCallback<ChatRequestBody, Pick<ChatTrackingData, "message">>;
} = {
  sql: (body) => ({
    query: body.query,
    models: getTableNamesFromSql(body.query),
  }),
  graphql: (body) => {
    const { operation, models } = parseGraphQLQuery(body.query);
    return {
      query: body.query,
      operation,
      models,
      operationName: body.operationName,
    };
  },
  chat: (body) => ({
    message: getLatestMessage(body.messages),
  }),
};

export const config = {
  matcher: ["/api/v1/sql", "/api/v1/graphql", "/api/v1/chat"],
};

function isValidApiType(type: string): type is ApiType {
  return API_TYPES.includes(type as ApiType);
}

export async function middleware(request: NextRequest): Promise<NextResponse> {
  const path = request.nextUrl.pathname;

  try {
    const user = await getUser(request);

    if (request.method === "OPTIONS") {
      return NextResponse.next();
    }

    const [, , , apiType] = path.split("/");

    if (!isValidApiType(apiType)) {
      logger.warn(`Invalid API type in path: ${apiType}`);
      return NextResponse.next();
    }

    if (user.role !== "anonymous") {
      await trackApiCall(request, user, apiType);
    }

    const requestHeaders = new Headers(request.headers);
    requestHeaders.set(
      "x-user-id",
      user.role === "anonymous" ? "" : user.userId,
    );
    requestHeaders.set("x-user-role", user.role);
    requestHeaders.set(
      "x-user-key-name",
      user.role === "anonymous" ? "" : user.keyName,
    );

    return NextResponse.next({
      request: {
        headers: requestHeaders,
      },
    });
  } catch (error) {
    logger.error("Middleware error:", error);
    return NextResponse.next();
  }
}

async function trackApiCall(
  request: NextRequest,
  user: Exclude<User, { role: "anonymous" }>,
  apiType: ApiType,
): Promise<void> {
  const path = request.nextUrl.pathname;
  const body = await getRequestBody(request);

  const baseData: BaseTrackingData = {
    type: apiType,
    endpoint: path,
    method: request.method,
    userId: user.userId,
    apiKeyName: user.keyName,
    host: user.host,
  };

  let trackingData: TrackingData;

  switch (apiType) {
    case "sql":
      if (body && isSqlBody(body)) {
        const sqlData = TRACK_CALLBACKS.sql(body);
        trackingData = { ...baseData, type: "sql", ...sqlData };
      } else {
        trackingData = { ...baseData, type: "sql", query: "", models: [] };
      }
      break;

    case "graphql":
      if (body && isGraphQLBody(body)) {
        const gqlData = TRACK_CALLBACKS.graphql(body);
        trackingData = { ...baseData, type: "graphql", ...gqlData };
      } else {
        trackingData = { ...baseData, type: "graphql", query: "" };
      }
      break;

    case "chat":
      if (body && isChatBody(body)) {
        const chatData = TRACK_CALLBACKS.chat(body);
        trackingData = { ...baseData, type: "chat", ...chatData };
      } else {
        trackingData = { ...baseData, type: "chat", message: "No messages" };
      }
      break;

    default: {
      const exhaustiveCheck: never = apiType;
      throw new Error(`Unhandled API type: ${exhaustiveCheck}`);
    }
  }

  await simpleCapture({
    distinctId: user.userId,
    event: EVENTS.API_CALL,
    properties: trackingData,
  });
}

async function getRequestBody(request: NextRequest): Promise<unknown | null> {
  try {
    if (request.method === "GET") return null;

    const clonedRequest = request.clone();
    return await clonedRequest.json();
  } catch {
    return null;
  }
}

function getLatestMessage(messages: ChatMessage[]): string {
  if (messages.length === 0) {
    return "Message not found";
  }
  const latestMessage = messages[messages.length - 1];
  return latestMessage.content || "Message not found";
}

export interface UserInfoFromHeaders {
  userId: string | null;
  role: string | null;
  keyName: string | null;
}

export function getUserFromHeaders(request: NextRequest): UserInfoFromHeaders {
  return {
    userId: request.headers.get("x-user-id"),
    role: request.headers.get("x-user-role"),
    keyName: request.headers.get("x-user-key-name"),
  };
}

// TODO(jabolo): use the PostHog SDK instead of this. Currently, the SDK
// does not work on edge middleware, so we are using a direct HTTP request.
interface UserEventCapture {
  distinctId: string;
  event: string;
  properties?: Record<string, any>;
  timestamp?: string;
}

/**
 * Simple capture function to send events to PostHog
 * - This is a direct HTTP request, not using the PostHog client
 * @param event
 */
async function simpleCapture(event: UserEventCapture): Promise<void> {
  const payload = {
    api_key: POSTHOG_KEY,
    event: event.event,
    distinct_id: event.distinctId,
    properties: event.properties || {},
    timestamp: event.timestamp || new Date().toISOString(),
  };

  try {
    const response = await fetch(`${POSTHOG_HOST_DIRECT}/capture/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(
        `PostHog capture failed: ${response.status} - ${errorText}`,
      );
    }
  } catch (error) {
    logger.error("Failed to capture PostHog event:", error);
  }
}
