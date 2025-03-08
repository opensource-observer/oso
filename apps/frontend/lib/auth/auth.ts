import "server-only";

import { type NextRequest } from "next/server";
import { supabasePrivileged } from "../clients/supabase";
import { User as SupabaseUser } from "@supabase/supabase-js";
import { serverAnalytics } from "../clients/segment";

type AnonUser = {
  role: "anonymous";
};

type User = {
  role: "user";
  userId: string;
  email?: string;
  name: string;
};

export type Session = AnonUser | User;

// HTTP headers
const AUTH_PREFIX = "bearer";

// Supabase schema
const API_KEY_TABLE = "api_keys";
const USER_ID_COLUMN = "user_id";
const API_KEY_COLUMN = "api_key";
const DELETED_COLUMN = "deleted_at";
const ALL_COLUMNS = `${USER_ID_COLUMN},${API_KEY_COLUMN},${DELETED_COLUMN}`;

const makeAnonUser = (): AnonUser => ({
  role: "anonymous",
});
const makeUser = (user: SupabaseUser): User => ({
  role: "user",
  userId: user.id,
  email: user.email,
  name: user.user_metadata.name,
});

async function getSession(request: NextRequest): Promise<Session> {
  const headers = request.headers;
  const auth = headers.get("authorization");

  // If no token provided, then return anonymous role
  if (!auth) {
    console.log(`auth: No token => anon`);
    return makeAnonUser();
  }

  // Get the token
  const trimmedAuth = auth.trim();
  const token = trimmedAuth.toLowerCase().startsWith(AUTH_PREFIX)
    ? trimmedAuth.slice(AUTH_PREFIX.length).trim()
    : trimmedAuth;

  // Get the user by API token
  const { data: keyData, error: keyError } = await supabasePrivileged
    .from(API_KEY_TABLE)
    .select(ALL_COLUMNS)
    .eq(API_KEY_COLUMN, token);

  if (keyError || !keyData) {
    console.warn(`auth: Error retrieving API keys => anon`, keyError);
    return makeAnonUser();
  }

  // Filter out inactive/deleted keys
  const activeKeys = keyData.filter((x) => !x.deleted_at);
  if (activeKeys.length < 1) {
    console.log(`auth: API key not valid => anon`);
    return makeAnonUser();
  }

  const userId = activeKeys[0].user_id;
  const { data: userData, error: userError } =
    await supabasePrivileged.auth.admin.getUserById(userId);
  if (userError || !userData) {
    console.warn(`auth: Error retrieving user data => anon`, userError);
    return makeAnonUser();
  }

  console.log(`/api/auth: API key and user valid valid => user`);
  return makeUser(userData.user);
}

export async function verifySession(request: NextRequest) {
  const session = await getSession(request);

  const trackParams = {
    event: "api_call",
    properties: {
      path: request.nextUrl.pathname,
    },
  };

  if (session.role === "user") {
    serverAnalytics!.track({
      userId: session.userId,
      ...trackParams,
    });
  } else {
    serverAnalytics!.track({
      anonymousId: crypto.randomUUID(),
      ...trackParams,
    });
  }

  return session;
}
