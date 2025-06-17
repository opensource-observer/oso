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
  const orgId = prompt.orgId;
  await using tracker = trackServerEvent(user);

  if (user.role === "anonymous") {
    logger.log(`/api/chat: User is anonymous`);
    return NextResponse.json(
      { error: "Authentication required" },
      { status: 401 },
    );
  }

  if (!orgId) {
    logger.log(`/api/chat: Missing orgId`);
    return NextResponse.json(
      { error: "Organization ID is required" },
      { status: 400 },
    );
  }

  const creditsDeducted =
    await CreditsService.checkAndDeductOrganizationCredits(
      user,
      orgId,
      TransactionType.CHAT_QUERY,
      "/api/v1/chat",
      { message: getLatestMessage(prompt.messages) },
    );

  if (!creditsDeducted) {
    logger.log(`/api/chat: Insufficient credits for user ${user.userId}`);
    return NextResponse.json(
      { error: "Insufficient credits" },
      { status: 402 },
    );
  }

  try {
    tracker.track(EVENTS.API_CALL, {
      type: "chat",
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
