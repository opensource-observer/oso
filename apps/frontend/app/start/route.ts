import { NextRequest, NextResponse } from "next/server";
import { logger } from "@/lib/logger";
import { getUser } from "@/lib/auth/auth";

export async function GET(req: NextRequest) {
  const user = await getUser(req);

  if (user.role === "anonymous") {
    logger.log(`/start: User is anonymous`);
    return NextResponse.redirect(new URL("/login", req.url));
  }
  const orgId = user.orgId;
  if (!orgId) {
    throw new Error("User has no orgId");
  }
  return NextResponse.redirect(new URL(`/orgs/${orgId}`, req.url));
}
