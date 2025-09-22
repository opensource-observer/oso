import { type NextRequest, NextResponse } from "next/server";
import { logger } from "@/lib/logger";
import { getUser } from "@/lib/auth/auth";
import { OSO_AGENT_URL } from "@/lib/config";
import { trackServerEvent } from "@/lib/analytics/track";
import { EVENTS } from "@/lib/types/posthog";
import {
  CreditsService,
  InsufficientCreditsError,
  TransactionType,
} from "@/lib/services/credits";
import { withPostHogTracking } from "@/lib/clients/posthog";

export const maxDuration = 60;
const COMPLETIONS_PATH = "/v0/chat/completions";
const COMPLETIONS_URL = new URL(COMPLETIONS_PATH, OSO_AGENT_URL).href;

const getLatestMessage = (messages: any[]) => {
  if (!Array.isArray(messages) || messages.length === 0) {
    return "Message not found";
  }
  const latestMessage = messages[messages.length - 1];
  const content = latestMessage?.content;
  return content || "Message not found";
};

export const POST = withPostHogTracking(async (req: NextRequest) => {
  const user = await getUser(req);
  const body = await req.json();
  const tracker = trackServerEvent(user);

  if (user.role === "anonymous") {
    logger.log(`/api/v1/chat/completions: User is anonymous`);
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
        "/api/v1/chat/completions",
        { message: getLatestMessage(body.messages) },
      );
    } catch (error) {
      if (error instanceof InsufficientCreditsError) {
        return NextResponse.json({ error: error.message }, { status: 402 });
      }
      logger.error(
        `/api/v1/chat/completions: Error tracking usage for user ${user.userId}:`,
        error,
      );
    }
  }

  tracker.track(EVENTS.API_CALL, {
    type: "chat_completions",
    message: getLatestMessage(body.messages),
  });

  const response = await fetch(COMPLETIONS_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Accept-Encoding": "identity",
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
});
