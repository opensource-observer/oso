import { NextResponse, type NextRequest } from "next/server";
import { createGoogleGenerativeAI } from "@ai-sdk/google";
import { spawn } from "@opensource-observer/utils";
import { withPostHog } from "../../../../lib/clients/posthog";
import { streamText } from "ai";
import { logger } from "../../../../lib/logger";
import { GOOGLE_AI_API_KEY } from "../../../../lib/config";
import { getUser } from "../../../../lib/auth/auth";

export const maxDuration = 60;
// TODO: replace this with the OSO agent
const google = createGoogleGenerativeAI({
  apiKey: GOOGLE_AI_API_KEY,
});
const model = google("gemini-2.5-pro-exp-03-25");

const getLatestMessage = (messages: any[]) => {
  if (!Array.isArray(messages) || messages.length === 0) {
    return "Message not found";
  }
  const latestMessage = messages[messages.length - 1];
  const content = latestMessage?.content;
  return content || "Message not found";
};

export async function POST(req: NextRequest) {
  const user = await getUser(req);
  const { messages } = await req.json();

  if (user.role === "anonymous") {
    return NextResponse.json(
      { error: "Authentication required" },
      { status: 401 },
    );
  }

  try {
    spawn(
      withPostHog(async (posthog) => {
        posthog.capture({
          distinctId: user.userId,
          event: "api_call",
          properties: {
            type: "chat",
            message: getLatestMessage(messages),
            apiKeyName: user.keyName,
            host: user.host,
          },
        });
      }),
    );
    const result = streamText({
      model,
      system: `You are a helpful SQL assistant for the OSO (OpenSource Observer) data lake.
Your purpose is to help users explore and analyze open source project data.
Always provide accurate and helpful responses about the OSO data.
When providing SQL queries, make sure they are valid for the OSO schema.
Use the query_oso, list_tables, and get_table_schema tools to provide accurate answers.
Format your SQL queries with proper indentation and keywords in uppercase.
When showing results, provide a brief explanation of what the data means. All the snippets
must be valid SQL queries in the Presto dialect. Do not use any other dialects or SQL engines.`,
      messages,
      maxSteps: 50,
      onFinish: async () => {},
      onError: async (error) => {
        logger.error("Error in chat route:", error);
      },
      maxTokens: 2000,
    });

    return result.toDataStreamResponse({
      sendUsage: true,
      sendReasoning: true,
    });
  } catch (error) {
    logger.error("Error in chat route:", error);
    return NextResponse.json(
      { error: "An error occurred processing your request" },
      { status: 500 },
    );
  }
}
