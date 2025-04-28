import "server-only";

import { type NextRequest } from "next/server";
import { supabasePrivileged } from "../clients/supabase";
import { User as SupabaseUser } from "@supabase/supabase-js";

type AnonUser = {
  role: "anonymous";
};
type UserDetails = {
  userId: string;
  email?: string;
  name: string;
};
type NormalUser = UserDetails & {
  role: "user";
};
type AdminUser = UserDetails & {
  role: "admin";
};

type User = AnonUser | NormalUser | AdminUser;

// HTTP headers
const AUTH_PREFIX = "bearer";

// Supabase schema
//// admin_users table
const ADMIN_USER_TABLE = "admin_users";
const ADMIN_USER_USER_ID_COLUMN = "user_id";
const ADMIN_USER_ALL_COLUMNS = `${ADMIN_USER_USER_ID_COLUMN}`;
//// api_keys table
const API_KEY_TABLE = "api_keys";
const API_KEY_USER_ID_COLUMN = "user_id";
const API_KEY_API_KEY_COLUMN = "api_key";
const API_KEY_DELETED_COLUMN = "deleted_at";
const API_KEY_ALL_COLUMNS = `${API_KEY_USER_ID_COLUMN},${API_KEY_API_KEY_COLUMN},${API_KEY_DELETED_COLUMN}`;

const makeAnonUser = (): AnonUser => ({
  role: "anonymous",
});
const makeNormalUser = (user: SupabaseUser): NormalUser => ({
  role: "user",
  userId: user.id,
  email: user.email,
  name: user.user_metadata.name,
});
const makeAdminUser = (user: SupabaseUser): AdminUser => ({
  role: "admin",
  userId: user.id,
  email: user.email,
  name: user.user_metadata.name,
});

async function getUser(request: NextRequest): Promise<User> {
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
    .select(API_KEY_ALL_COLUMNS)
    .eq(API_KEY_API_KEY_COLUMN, token);

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
  const user = userData.user;

  // Check for admins
  const { data: adminData, error: adminError } = await supabasePrivileged
    .from(ADMIN_USER_TABLE)
    .select(ADMIN_USER_ALL_COLUMNS)
    .eq(ADMIN_USER_USER_ID_COLUMN, userId);

  if (adminError || !adminData) {
    console.warn(
      `auth: Valid key, error retrieving admin users => user`,
      adminError,
    );
    return makeNormalUser(user);
  } else if (adminData.length > 0) {
    console.log(`auth: Valid key and admin => admin`);
    return makeAdminUser(user);
  }

  console.log(`auth: API key and user valid => user`);
  return makeNormalUser(userData.user);
}

/**
async function verifySession(request: NextRequest) {
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
*/

export { getUser };
export type { AnonUser, NormalUser, AdminUser, User };
