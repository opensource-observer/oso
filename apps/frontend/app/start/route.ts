import { NextRequest, NextResponse } from "next/server";
import { logger } from "@/lib/logger";
import { getUser } from "@/lib/auth/auth";

export async function GET(req: NextRequest) {
  const user = await getUser(req);

  if (user.role === "anonymous") {
    logger.log(`/start: User is anonymous`);
    return NextResponse.redirect(new URL("/login", req.url));
  }
  const orgName = user.orgName;
  return NextResponse.redirect(new URL(`/${orgName}`, req.url));
}
