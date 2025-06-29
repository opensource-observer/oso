import { NextResponse, type NextRequest } from "next/server";
import { getUser } from "@/lib/auth/auth";
import { assertNever } from "@opensource-observer/utils";
//import { logger } from "../../../lib/logger";

// Next.js route control
export const runtime = "edge"; // 'nodejs' (default) | 'edge'
//export const dynamic = "force-dynamic";
export const revalidate = 0;

// HTTP headers
const CACHE_CONTROL = "max-age=3600"; // in seconds

// Helper functions for creating responses suitable for Hasura
const makeAnonRole = () => ({
  "x-hasura-role": "anonymous",
});
const makeUserRole = (userId: string) => ({
  //"x-hasura-default-role": "user",
  //"x-hasura-allowed-roles": ["user"],
  "x-hasura-role": "user",
  "x-hasura-user-id": userId,
  "cache-control": CACHE_CONTROL,
});
const makeAdminRole = (userId: string) => ({
  "x-hasura-role": "admin",
  "x-hasura-user-id": userId,
  "cache-control": CACHE_CONTROL,
});

/**
 * Authentication check for Hasura GraphQL API
 * Hasura will check this webhook on inbound requests
 * @param request
 * @returns
 */
export async function GET(request: NextRequest) {
  const user = await getUser(request);
  if (user.role === "anonymous") {
    return NextResponse.json(makeAnonRole());
  } else if (user.role === "user") {
    return NextResponse.json(makeUserRole(user.userId));
  } else if (user.role === "admin") {
    return NextResponse.json(makeAdminRole(user.userId));
  } else {
    assertNever(user);
  }
}
