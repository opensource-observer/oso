import { type NextRequest, NextResponse } from "next/server";
import OpenAI from "openai";
import { logger } from "@/lib/logger";
import { getUser } from "@/lib/auth/auth";
import { trackServerEvent } from "@/lib/analytics/track";
import { EVENTS } from "@/lib/types/posthog";

export const runtime = "nodejs";
export const maxDuration = 60;

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

async function createChatCompletion(openai: OpenAI, content: string) {
  return await openai.chat.completions.create({
    messages: [{ role: "user", content }],
    model: "oso/semantic",
    stream: false,
  });
}

async function createResponse(openai: OpenAI, content: string) {
  const response = await openai.responses.create({
    input: content,
    model: "oso/semantic",
    store: false,
  });

  return {
    id: response.id,
    object: "chat.completion",
    created: Math.floor(response.created_at / 1000),
    model: response.model,
    choices: [
      {
        index: 0,
        message: {
          role: "assistant",
          content: response.output_text || "",
          refusal: null,
        },
        finish_reason: "stop",
      },
    ],
    usage: response.usage,
  };
}

export async function POST(req: NextRequest) {
  const user = await getUser(req);
  const baseURL = new URL("/api/v1/", req.url).href;
  const { searchParams } = new URL(req.url);
  const useResponses = searchParams.get("api") === "responses";
  await using tracker = trackServerEvent(user);

  const {
    prompt,
    includeOtherCode,
    language,
    code,
    osoApiKey: apiKey,
  }: MarimoCompletionRequest & { osoApiKey?: string } = await req.json();

  const openai = new OpenAI({
    apiKey,
    baseURL,
    defaultHeaders: {
      "Accept-Encoding": "identity",
    },
  });

  try {
    tracker.track(EVENTS.API_CALL, {
      type: "marimo_ai_completion",
      useResponses,
      prompt,
      includeOtherCode,
      language,
      code,
    });

    const result = useResponses
      ? await createResponse(openai, prompt)
      : await createChatCompletion(openai, prompt);

    return NextResponse.json(result);
  } catch (error: any) {
    logger.error("Completion error", error);
    return NextResponse.json(
      { error: "completion_failed" },
      { status: error?.status || 500 },
    );
  }
}
