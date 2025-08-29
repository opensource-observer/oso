import { type NextRequest, NextResponse } from "next/server";
import { logger } from "@/lib/logger";
import { getUser } from "@/lib/auth/auth";

export async function GET(req: NextRequest) {
  const user = await getUser(req);

  if (user.role === "anonymous") {
    logger.log(`/api/chat: User is anonymous`);
    return NextResponse.redirect("/login");
  }
  const orgId = user.orgId;
  return NextResponse.redirect(`/orgs/${orgId}`);
}
