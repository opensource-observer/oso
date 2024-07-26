import { NextResponse, type NextRequest } from "next/server";
import { supabasePrivileged } from "../../../../lib/clients/supabase";
import { jwtDecode } from "jwt-decode";
//import { logger } from "../../../lib/logger";

// Next.js route control
export const runtime = "edge"; // 'nodejs' (default) | 'edge'
//export const dynamic = "force-dynamic";
export const revalidate = 0;

// HTTP headers
const CACHE_CONTROL = "max-age=3600"; // in seconds
const HASURA_USER_ID_KEY = "x-hasura-user-id";
const AUTH_PREFIX = "bearer";

// Supabase schema
const DATA_COLLECTIVE_TABLE = "data_collective";
const API_KEY_TABLE = "api_keys";
const USER_ID_COLUMN = "user_id";
const API_KEY_COLUMN = "api_key";
const DELETED_COLUMN = "deleted_at";
const ALL_COLUMNS = `${USER_ID_COLUMN},${API_KEY_COLUMN},${DELETED_COLUMN}`;

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
const makeDevRole = (userId: string) => ({
  "x-hasura-role": "developer",
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
  const headers = request.headers;
  const auth = headers.get("authorization");

  // If no token provided, then return anonymous role
  if (!auth) {
    console.log(`/api/auth: No token => anon`);
    return NextResponse.json(makeAnonRole());
  }

  // Get the token
  const trimmedAuth = auth.trim();
  const token = trimmedAuth.toLowerCase().startsWith(AUTH_PREFIX)
    ? trimmedAuth.slice(AUTH_PREFIX.length).trim()
    : trimmedAuth;

  // Try JWT decoding
  try {
    // @TODO replace this library with one that verifies.
    // Other existing npm libraries seem to struggle in an edge runtime.
    const decoded: any = jwtDecode(token);
    //console.log("JWT token: ", decoded);
    const userId = decoded.app_metadata?.[HASURA_USER_ID_KEY];
    if (userId) {
      console.log(`/api/auth: valid JWT token => user`);
      return NextResponse.json(makeUserRole(userId));
    }
  } catch (e) {
    console.warn("JWT decoding error: ", e);
  }

  // Get the user by API token
  const { data: keyData, error: keyError } = await supabasePrivileged
    .from(API_KEY_TABLE)
    .select(ALL_COLUMNS)
    .eq(API_KEY_COLUMN, token);

  if (keyError || !keyData) {
    console.warn(`/api/auth: Error retrieving API keys => anon`, keyError);
    return NextResponse.json(makeAnonRole());
  }

  // Filter out inactive/deleted keys
  const activeKeys = keyData.filter((x) => !x.deleted_at);
  if (activeKeys.length < 1) {
    console.log(`/api/auth: API key not valid => anon`);
    return NextResponse.json(makeAnonRole());
  }

  // Check for data collective membership
  const userId = activeKeys[0].user_id;
  const { data: collectiveData, error: collectiveError } =
    await supabasePrivileged
      .from(DATA_COLLECTIVE_TABLE)
      .select(USER_ID_COLUMN)
      .eq(USER_ID_COLUMN, userId);

  if (collectiveError || !collectiveData) {
    console.warn(
      `/api/auth: Valid key, error retrieving data collective membership => user`,
      collectiveError,
    );
    return NextResponse.json(makeUserRole(userId));
  } else if (collectiveData.length < 1) {
    // Not a member
    console.log(`/api/auth: Valid key, not data collective member => user`);
    return NextResponse.json(makeUserRole(userId));
  }

  // Passes all checks, elevate to developer role
  console.log(`/api/auth: API key valid => developer`);
  return NextResponse.json(makeDevRole(userId));
}
