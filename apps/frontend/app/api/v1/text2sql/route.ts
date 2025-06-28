import { type NextRequest, NextResponse } from "next/server";
import { logger } from "@/lib/logger";
import { getUser } from "@/lib/auth/auth";
import { OSO_AGENT_URL } from "@/lib/config";
import { trackServerEvent } from "@/lib/analytics/track";
import { EVENTS } from "@/lib/types/posthog";
import { CreditsService, TransactionType } from "@/lib/services/credits";

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
  await using tracker = trackServerEvent(user);

  if (user.role === "anonymous") {
    logger.log(`/api/v1/text2sql: User is anonymous`);
    return NextResponse.json(
      { error: "Authentication required" },
      { status: 401 },
    );
  }

  const orgId = user.orgId;

  if (orgId) {
    try {
      await CreditsService.checkAndDeductOrganizationCredits(
        user,
        orgId,
        TransactionType.TEXT2SQL,
        "/api/v1/text2sql",
        { message: getLatestMessage(prompt.messages) },
      );
    } catch (error) {
      logger.error(
        `/api/v1/text2sql: Error tracking usage for user ${user.userId}:`,
        error,
      );
    }
  }

  try {
    tracker.track(EVENTS.API_CALL, {
      type: "text2sql",
      message: getLatestMessage(prompt.messages),
    });

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
