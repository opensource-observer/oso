import { type NextRequest, NextResponse } from "next/server";
import { logger } from "@/lib/logger";
import { getUser, signOsoJwt } from "@/lib/auth/auth";
import { OSO_AGENT_URL } from "@/lib/config";
import { trackServerEvent } from "@/lib/analytics/track";
import { EVENTS } from "@/lib/types/posthog";
import { CreditsService, TransactionType } from "@/lib/services/credits";
import { createServerClient } from "@/lib/supabase/server";

export const maxDuration = 60;
const CHAT_PATH = "/v0/chat";
const CHAT_URL = new URL(CHAT_PATH, OSO_AGENT_URL).href;

const getLatestMessage = (messages: any[]) => {
  if (!Array.isArray(messages) || messages.length === 0) {
    return "Message not found";
  }
  const latestMessage = messages[messages.length - 1];
  const content = latestMessage?.content;
  return content || "Message not found";
};

export async function POST(req: NextRequest) {
  const supabaseClient = await createServerClient();
  const user = await getUser(req);
  const { chatId, ...prompt } = await req.json();
  await using tracker = trackServerEvent(user);

  if (user.role === "anonymous") {
    logger.log(`/api/chat: User is anonymous`);
    return NextResponse.json(
      { error: "Authentication required" },
      { status: 401 },
    );
  }

  const { data, error } = await supabaseClient
    .from("chat_history")
    .select("org_id(*)")
    .eq("id", chatId)
    .single();

  if (!data || error) {
    return NextResponse.json(
      {
        error: `Error fetching organization for chat with id ${chatId}: ${error.message}`,
      },
      { status: 500 },
    );
  }

  const org = data.org_id;

  try {
    await CreditsService.checkAndDeductOrganizationCredits(
      user,
      org.id,
      TransactionType.CHAT_QUERY,
      "/api/v1/chat",
      { message: getLatestMessage(prompt.messages) },
    );
  } catch (error) {
    logger.error(
      `/api/chat: Error tracking usage for user ${user.userId}:`,
      error,
    );
  }

  const osoToken = await signOsoJwt(user, {
    orgId: org.id,
    orgName: org.org_name,
  });

  try {
    tracker.track(EVENTS.API_CALL, {
      type: "chat",
      message: getLatestMessage(prompt.messages),
    });

    const response = await fetch(CHAT_URL, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${osoToken}`,
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
