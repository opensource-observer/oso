import { NextResponse, type NextRequest } from "next/server";
import { spawn } from "@opensource-observer/utils";
import { withPostHog } from "../../../../lib/clients/posthog";
import { logger } from "../../../../lib/logger";
import { getUser } from "../../../../lib/auth/auth";
import { OSO_AGENT_URL } from "../../../../lib/config";

export const maxDuration = 60;

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
  const prompt = await req.json();

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
            message: getLatestMessage(prompt.messages),
            apiKeyName: user.keyName,
            host: user.host,
          },
        });
      }),
    );

    const response = await fetch(OSO_AGENT_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(prompt),
    });

    return new Response(await response.text(), { status: response.status });
  } catch (error) {
    logger.error("Error in chat route:", error);
    return NextResponse.json(
      { error: "An error occurred processing your request" },
      { status: 500 },
    );
  }
}
