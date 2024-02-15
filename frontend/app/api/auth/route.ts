import { NextResponse, type NextRequest } from "next/server";
//import { logger } from "../../../lib/logger";

export const runtime = "edge"; // 'nodejs' (default) | 'edge'
//export const dynamic = "force-dynamic";
export const revalidate = 0;
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

  console.log("Authorization: ", auth);

  // Default to anonymous role
  return NextResponse.json(makeAnonRole());
}
