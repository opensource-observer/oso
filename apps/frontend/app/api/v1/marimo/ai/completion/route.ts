import { type NextRequest, NextResponse } from "next/server";
import OpenAI from "openai";
import { logger } from "@/lib/logger";
import { getUser } from "@/lib/auth/auth";
import { trackServerEvent } from "@/lib/analytics/track";
import { EVENTS } from "@/lib/types/posthog";
import { withPostHogTracking } from "@/lib/clients/posthog";

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
  model: string;
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

async function createChatCompletion(
  openai: OpenAI,
  content: string,
  model: string,
) {
  return await openai.chat.completions.create({
    messages: [{ role: "user", content }],
    model: model,
    stream: true,
  });
}

async function createResponse(openai: OpenAI, content: string, model: string) {
  return await openai.responses.create({
    input: content,
    model: model,
    store: false,
    stream: true,
  });
}

function createStreamingResponse<T>(
  stream: AsyncIterable<T>,
  extractContent: (chunk: T) => string | null,
): Response {
  const encoder = new TextEncoder();
  const readable = new ReadableStream({
    async start(controller) {
      try {
        for await (const chunk of stream) {
          const content = extractContent(chunk);
          if (content) {
            controller.enqueue(encoder.encode(content));
          }
        }
        controller.close();
      } catch (error) {
        controller.error(error);
      }
    },
  });

  return new Response(readable, {
    headers: {
      "Content-Type": "application/json",
    },
  });
}

export const POST = withPostHogTracking(async (req: NextRequest) => {
  const user = await getUser(req);
  const baseURL = new URL("/api/v1/", req.url).href;
  const { searchParams } = new URL(req.url);
  const useResponses = searchParams.get("api") === "responses";
  const tracker = trackServerEvent(user);

  const {
    prompt,
    includeOtherCode,
    language,
    code,
    osoApiKey: apiKey,
    model,
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

    if (useResponses) {
      const stream = await createResponse(openai, prompt, model);

      return createStreamingResponse(stream, (chunk) =>
        chunk.type === "response.output_text.delta" ? chunk.delta : null,
      );
    }

    const stream = await createChatCompletion(openai, prompt, model);

    return createStreamingResponse(
      stream,
      (chunk) => chunk.choices[0]?.delta?.content || null,
    );
  } catch (error: any) {
    logger.error("Completion error", error);
    return NextResponse.json(
      { error: "completion_failed" },
      { status: error?.status || 500 },
    );
  }
});
