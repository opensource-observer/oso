import { NextResponse, type NextRequest } from "next/server";
import { verify } from "jsonwebtoken";
import { supabasePrivileged } from "../../../lib/clients/supabase";
import { SUPABASE_JWT_SECRET } from "../../../lib/config";
//import { logger } from "../../../lib/logger";

export const runtime = "edge"; // 'nodejs' (default) | 'edge'
//export const dynamic = "force-dynamic";
export const revalidate = 0;
const API_KEY_TABLE = "api_keys";
const USER_ID_COLUMN = "user_id";
const API_KEY_COLUMN = "api_key";
const ALL_COLUMNS = `${USER_ID_COLUMN},${API_KEY_COLUMN}`;
const makeAnonRole = () => ({
  "x-hasura-role": "anonymous",
});
/**
const makeUserRole = (userId: string) => ({
  "x-hasura-default-role": "user",
  "x-hasura-allowed-roles": ["user"],
  "x-hasura-user-id": userId,
});
const makeDevRole = (userId: string) => ({
  "x-hasura-default-role": "developer",
  "x-hasura-allowed-roles": ["developer", "user"],
  "x-hasura-user-id": userId,
});
**/

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

  const trimmedAuth = auth.trim();
  const token = trimmedAuth.toLowerCase().startsWith("bearer")
    ? trimmedAuth.slice(6).trim()
    : trimmedAuth;

  try {
    const decoded = verify(token, SUPABASE_JWT_SECRET);
    console.log("JWT decoded: ", decoded);
    //const userId = decoded.sub;
    //return NextResponse.json(makeUserRole(userId));
  } catch (e) {
    console.warn("Not a JWT token", e);
  }

  const { data, error } = await supabasePrivileged
    .from(API_KEY_TABLE)
    .select(ALL_COLUMNS)
    .eq(API_KEY_COLUMN, token);

  console.log(data, error);

  // Default to anonymous role
  return NextResponse.json(makeAnonRole());
}
