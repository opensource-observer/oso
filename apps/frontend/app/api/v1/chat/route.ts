import { NextResponse, type NextRequest } from "next/server";
import { logger } from "../../../../lib/logger";
import { OSO_AGENT_URL } from "../../../../lib/config";

export const maxDuration = 60;

export async function POST(req: NextRequest) {
  const userId = req.headers.get("x-user-id");
  const userRole = req.headers.get("x-user-role");
  const keyName = req.headers.get("x-user-key-name");

  const user = {
    userId: userId || "",
    role: userRole || "anonymous",
    keyName: keyName || "",
  };

  const prompt = await req.json();

  if (user.role === "anonymous") {
    return NextResponse.json(
      { error: "Authentication required" },
      { status: 401 },
    );
  }

  try {
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
