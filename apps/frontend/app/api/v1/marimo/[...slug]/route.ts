import { type NextRequest, NextResponse } from "next/server";
import OpenAI from "openai";
import { logger } from "@/lib/logger";
import { OSO_AGENT_URL, OSO_API_KEY } from "@/lib/config";

export const runtime = "nodejs";
export const maxDuration = 60;

type HttpMethod = "GET" | "POST" | "PUT" | "DELETE" | "PATCH";
type RouteContext = { req: NextRequest; path: string };
type RouteHandler = {
  method: HttpMethod;
  description: string;
  handler: (context: RouteContext) => Promise<NextResponse>;
};

const OPENAI_BASE_PATH = "/v0";
const OPENAI_BASE_URL = new URL(OPENAI_BASE_PATH, OSO_AGENT_URL).href;

const openai = new OpenAI({
  apiKey: OSO_API_KEY,
  baseURL: OPENAI_BASE_URL,
});

interface MarimoCompletionRequest {
  prompt: string;
  includeOtherCode: string;
  context: {
    plainText: string;
    schema: SchemaTable[];
    variables: VariableContext[];
  };
  language: "python" | "sql" | "markdown";
  code: string;
}

interface SchemaTable {
  name: string;
  columns: {
    name: string;
    type: string;
    sample_values: unknown[];
  }[];
}

interface VariableContext {
  name: string;
  value_type: string;
  preview_value: unknown;
}

const createCompletionHandler =
  (): RouteHandler["handler"] =>
  async ({ req }) => {
    try {
      const marimoRequest: MarimoCompletionRequest = await req.json();
      const completion = await openai.chat.completions.create({
        messages: [{ role: "user", content: marimoRequest.prompt }],
        model: "oso/semantic",
        stream: false,
      });

      return NextResponse.json(completion);
    } catch (error: any) {
      logger.error?.("Completion error", error);
      return NextResponse.json(
        { error: "completion_failed" },
        { status: error?.status || 500 },
      );
    }
  };

const createInfoHandler = (): RouteHandler["handler"] => async () => {
  const endpoints = Object.fromEntries(
    Array.from(routes.entries()).map(([path, handler]) => [
      path,
      {
        method: handler.method,
        description: handler.description,
        path: `/api/v1/marimo/${path}`,
      },
    ]),
  );

  return NextResponse.json({
    message: "Available Marimo API endpoints",
    endpoints,
    total: Object.keys(endpoints).length,
  });
};

const routes = new Map<string, RouteHandler>([
  [
    "ai/completion",
    {
      method: "POST",
      description: "OpenAI-compatible chat completion endpoint",
      handler: createCompletionHandler(),
    },
  ],
  [
    "info",
    {
      method: "GET",
      description: "Lists all available endpoints and their methods",
      handler: createInfoHandler(),
    },
  ],
]);

const getPath = (params: { slug: string[] }) => (params?.slug ?? []).join("/");

const createErrorResponse = (error: string, message: string, status: number) =>
  NextResponse.json({ error, message }, { status });

async function handleRequest(
  req: NextRequest,
  params: { slug: string[] },
  method: HttpMethod,
): Promise<NextResponse> {
  const path = getPath(params);
  logger.log(`${method} /api/v1/marimo/${path}`);

  const route = routes.get(path);

  if (!route) {
    return createErrorResponse("not_found", `Endpoint ${path} not found`, 404);
  }

  if (route.method !== method) {
    return createErrorResponse(
      "method_not_allowed",
      `${method} not supported for ${path}. Use ${route.method}`,
      405,
    );
  }

  return route.handler({ req, path });
}

export async function GET(
  req: NextRequest,
  { params }: { params: { slug: string[] } },
) {
  return handleRequest(req, params, "GET");
}

export async function POST(
  req: NextRequest,
  { params }: { params: { slug: string[] } },
) {
  return handleRequest(req, params, "POST");
}
