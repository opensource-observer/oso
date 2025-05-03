import "server-only";

import { type NextRequest } from "next/server";
import { supabasePrivileged, createSupabaseClient } from "../clients/supabase";
import { User as SupabaseUser } from "@supabase/supabase-js";
import { AnonUser, NormalUser, AdminUser, AuthUser, User } from "../types/user";

const DEFAULT_KEY_NAME = "login";

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
const API_KEY_NAME_COLUMN = "name";
const API_KEY_API_KEY_COLUMN = "api_key";
const API_KEY_DELETED_COLUMN = "deleted_at";
const API_KEY_ALL_COLUMNS = `${API_KEY_USER_ID_COLUMN},${API_KEY_NAME_COLUMN},${API_KEY_API_KEY_COLUMN},${API_KEY_DELETED_COLUMN}`;

const makeAnonUser = (host: string | null): AnonUser => ({
  role: "anonymous",
  host,
});
const makeNormalUser = (
  user: SupabaseUser,
  keyName: string,
  host: string | null,
): NormalUser => ({
  role: "user",
  userId: user.id,
  keyName,
  host,
  email: user.email,
  name: user.user_metadata.name,
});
const promoteAdmin = (user: AuthUser): AdminUser => ({
  ...user,
  role: "admin",
});

async function getUserByApiKey(
  token: string,
  host: string | null,
): Promise<User> {
  const { data: keyData, error: keyError } = await supabasePrivileged
    .from(API_KEY_TABLE)
    .select(API_KEY_ALL_COLUMNS)
    .eq(API_KEY_API_KEY_COLUMN, token);

  if (keyError || !keyData) {
    console.warn(`auth: Error retrieving API keys => anon`, keyError);
    return makeAnonUser(host);
  }

  // Filter out inactive/deleted keys
  const activeKeys = keyData.filter((x) => !x.deleted_at);
  if (activeKeys.length < 1) {
    console.log(`auth: API key not valid => anon`);
    return makeAnonUser(host);
  }

  const activeKey = activeKeys[0];
  const userId = activeKey.user_id;
  const { data: userData, error: userError } =
    await supabasePrivileged.auth.admin.getUserById(userId);
  if (userError || !userData) {
    console.warn(`auth: Error retrieving user data => anon`, userError);
    return makeAnonUser(host);
  }

  console.log(`auth: API key and user valid => user`);
  return makeNormalUser(userData.user, activeKey.name, host);
}

async function getUserByJwt(token: string, host: string | null): Promise<User> {
  const { data, error } = await createSupabaseClient().auth.getUser(token);
  if (error) {
    //console.warn(`auth: Error retrieving user by JWT => anon`, error);
    console.warn(`auth: Error retrieving user by JWT => anon`);
    return makeAnonUser(host);
  }

  console.log(`auth: JWT token valid => user`);
  return makeNormalUser(data.user, DEFAULT_KEY_NAME, host);
}

async function getUser(request: NextRequest): Promise<User> {
  const headers = request.headers;
  const host = getHost(request);
  const auth = headers.get("authorization");

  // If no token provided, then return anonymous role
  if (!auth) {
    console.log(`auth: No token => anon`);
    return makeAnonUser(host);
  }

  // Get the token
  const trimmedAuth = auth.trim();
  const token = trimmedAuth.toLowerCase().startsWith(AUTH_PREFIX)
    ? trimmedAuth.slice(AUTH_PREFIX.length).trim()
    : trimmedAuth;

  // Try to get the user by JWT token first
  const jwtUser = await getUserByJwt(token, host);
  // If the user not found, try to get the user by API key
  const user =
    jwtUser.role === "anonymous" ? await getUserByApiKey(token, host) : jwtUser;

  // Short circuit if the user is anonymous
  if (user.role === "anonymous") {
    return user;
  }

  // Check for admins
  const { data: adminData, error: adminError } = await supabasePrivileged
    .from(ADMIN_USER_TABLE)
    .select(ADMIN_USER_ALL_COLUMNS)
    .eq(ADMIN_USER_USER_ID_COLUMN, user.userId);
  if (adminError || !adminData) {
    console.warn(
      `auth: Valid key, error retrieving admin users => user`,
      adminError,
    );
    return user;
  } else if (adminData.length > 0) {
    console.log(`auth: Valid key and admin => admin`);
    return promoteAdmin(user);
  }

  return user;
}

function getHost(req: NextRequest) {
  const host = req.headers.get("host");
  const forwardedHost = req.headers.get("x-forwarded-host");
  return forwardedHost ?? host;
}

export { getUser };
