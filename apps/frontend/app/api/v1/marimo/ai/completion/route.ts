import { type NextRequest, NextResponse } from "next/server";
import OpenAI from "openai";
import { logger } from "@/lib/logger";
import { OSO_API_KEY } from "@/lib/config";

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
  const baseURL = new URL("/api/v1/", req.url).href;
  const { searchParams } = new URL(req.url);
  const useResponses = searchParams.get("api") === "responses";

  const openai = new OpenAI({
    apiKey: OSO_API_KEY,
    baseURL,
    defaultHeaders: {
      "Accept-Encoding": "identity",
    },
  });

  try {
    const { prompt: content }: MarimoCompletionRequest = await req.json();

    const result = useResponses
      ? await createResponse(openai, content)
      : await createChatCompletion(openai, content);

    return NextResponse.json(result);
  } catch (error: any) {
    logger.error("Completion error", error);
    return NextResponse.json(
      { error: "completion_failed" },
      { status: error?.status || 500 },
    );
  }
}
