import { NextResponse, type NextRequest } from "next/server";
import { supabasePrivileged } from "../../../lib/clients/supabase";
//import { logger } from "../../../lib/logger";

export const runtime = "edge"; // 'nodejs' (default) | 'edge'
//export const dynamic = "force-dynamic";
export const revalidate = 0;
const CACHE_CONTROL = "max-age=3600"; // in seconds
const DATA_COLLECTIVE_TABLE = "data_collective";
const API_KEY_TABLE = "api_keys";
const USER_ID_COLUMN = "user_id";
const API_KEY_COLUMN = "api_key";
const DELETED_COLUMN = "deleted_at";
const ALL_COLUMNS = `${USER_ID_COLUMN},${API_KEY_COLUMN},${DELETED_COLUMN}`;
const makeAnonRole = () => ({
  "x-hasura-role": "anonymous",
});
/**
const makeUserRole = (userId: string) => ({
  "x-hasura-default-role": "user",
  "x-hasura-allowed-roles": ["user"],
  "x-hasura-user-id": userId,
});
**/
const makeDevRole = (userId: string) => ({
  "x-hasura-role": "developer",
  "x-hasura-user-id": userId,
  "cache-control": CACHE_CONTROL,
});

/**
 * This will return an array of all artifacts
 * This is currently fetched by Algolia to build the search index
 * @param _request
 * @returns
 */
export async function GET(request: NextRequest) {
  const headers = request.headers;
  const auth = headers.get("authorization");

  // If no token provided, then return anonymous role
  if (!auth) {
    return NextResponse.json(makeAnonRole());
  }

  // Get the token
  const trimmedAuth = auth.trim();
  const token = trimmedAuth.toLowerCase().startsWith("bearer")
    ? trimmedAuth.slice(6).trim()
    : trimmedAuth;

  // Get the user
  const { data: keyData, error: keyError } = await supabasePrivileged
    .from(API_KEY_TABLE)
    .select(ALL_COLUMNS)
    .eq(API_KEY_COLUMN, token);

  if (keyError || !keyData) {
    console.warn("Error retrieving API keys", keyError);
    return NextResponse.json(makeAnonRole());
  }

  const activeKeys = keyData.filter((x) => !x.deleted_at);
  if (activeKeys.length < 1) {
    return NextResponse.json(makeAnonRole());
  }

  const userId = activeKeys[0].user_id;

  // Check for data collective membership
  const { data: collectiveData, error: collectiveError } =
    await supabasePrivileged
      .from(DATA_COLLECTIVE_TABLE)
      .select(USER_ID_COLUMN)
      .eq(USER_ID_COLUMN, userId);

  if (collectiveError || !collectiveData) {
    console.warn(
      "Error retrieving data collective membership",
      collectiveError,
    );
    return NextResponse.json(makeAnonRole());
  } else if (collectiveData.length < 1) {
    // Not a member
    return NextResponse.json(makeAnonRole());
  }

  // Passes all checks, elevate to developer role
  return NextResponse.json(makeDevRole(userId));
}
