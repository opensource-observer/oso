import { type NextRequest, NextResponse } from "next/server";
import { logger } from "@/lib/logger";
import { getUser } from "@/lib/auth/auth";
import { OSO_AGENT_URL } from "@/lib/config";
import { trackServerEvent } from "@/lib/analytics/track";
import { EVENTS } from "@/lib/types/posthog";
import { CreditsService, TransactionType } from "@/lib/services/credits";

export const maxDuration = 60;
const RESPONSES_PATH = "/v0/responses";
const RESPONSES_URL = new URL(RESPONSES_PATH, OSO_AGENT_URL).href;

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
  const body = await req.json();
  await using tracker = trackServerEvent(user);

  if (user.role === "anonymous") {
    logger.log(`/api/v1/chat/responses: User is anonymous`);
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
        TransactionType.AGENT_QUERY,
        "/api/v1/chat/responses",
        { message: getLatestMessage(body.messages) },
      );
    } catch (error) {
      logger.error(
        `/api/v1/chat/responses: Error tracking usage for user ${user.userId}:`,
        error,
      );
    }
  }

  tracker.track(EVENTS.API_CALL, {
    type: "chat_responses",
    message: getLatestMessage(body.messages),
  });

  const response = await fetch(RESPONSES_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (body.stream) {
    return new Response(response.body, {
      status: response.status,
      headers: {
        "Content-Type": "text/plain; charset=utf-8",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
        ...Object.fromEntries(response.headers.entries()),
      },
    });
  }

  return new Response(await response.text(), {
    status: response.status,
    headers: response.headers,
  });
}
