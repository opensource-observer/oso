import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { verifySession } from "./lib/auth/auth";

export default async function middleware(request: NextRequest) {
  await verifySession(request);

  return NextResponse.next();
}

export const config = {
  matcher: "/api/:path*",
};
