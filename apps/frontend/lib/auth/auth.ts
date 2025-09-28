import "server-only";
import { type NextRequest } from "next/server";
import { createAdminClient } from "@/lib/supabase/admin";
import { createServerClient } from "@/lib/supabase/server";
import { SupabaseClient, User as SupabaseUser } from "@supabase/supabase-js";
import {
  AnonUser,
  NormalOrgUser,
  AdminOrgUser,
  AuthOrgUser,
  OrgUser,
  OrganizationDetails,
  OrgRole,
  AuthOrgUserSchema,
  User,
  NormalUser,
  AdminUser,
  AuthUser,
  OrgUserSchema,
  UserSchema,
} from "@/lib/types/user";
import { Database } from "@/lib/types/supabase";
import { OSO_JWT_SECRET } from "@/lib/config";
import { SignJWT, jwtVerify } from "jose";

// Constants
const DEFAULT_KEY_NAME = "login";

// HTTP headers
const AUTH_PREFIX = "bearer";

// Database schema constants
const TABLES = {
  ADMIN_USERS: "admin_users",
  API_KEYS: "api_keys",
  ORGANIZATIONS: "organizations",
  USERS_BY_ORG: "users_by_organization",
} as const;

const COLUMNS = {
  ADMIN_USERS: {
    USER_ID: "user_id",
  },
  API_KEYS: {
    USER_ID: "user_id",
    NAME: "name",
    API_KEY: "api_key",
    DELETED_AT: "deleted_at",
    ORG_ID: "org_id",
  },
  ORGANIZATIONS: {
    ID: "id",
    NAME: "org_name",
    CREATED_BY: "created_by",
    DELETED_AT: "deleted_at",
  },
  USERS_BY_ORG: {
    USER_ID: "user_id",
    ORG_ID: "org_id",
    ROLE: "user_role",
    DELETED_AT: "deleted_at",
  },
} as const;

const supabasePrivileged = createAdminClient();

/**
 * Factory function for anonymous users
 */
const makeAnonUser = (host: string | null): AnonUser => ({
  role: "anonymous",
  host,
});

/**
 * Factory function for normal users
 */
const makeNormalUser = (
  user: SupabaseUser,
  keyName: string,
  host: string | null,
  orgDetails: OrganizationDetails | undefined,
): NormalOrgUser | NormalUser => {
  if (orgDetails) {
    const normalOrgUser: NormalOrgUser = {
      role: "user",
      host,
      userId: user.id,
      keyName,
      email: user.email,
      name: user.user_metadata.name,
      orgId: orgDetails.orgId,
      orgName: orgDetails.orgName,
      orgRole: orgDetails.orgRole,
    };

    return normalOrgUser;
  }

  const normalUser: NormalUser = {
    role: "user",
    host,
    userId: user.id,
    keyName,
    email: user.email,
    name: user.user_metadata.name,
  };

  return normalUser;
};

/**
 * Promote a user to admin role
 */
function promoteAdmin(user: AuthUser): AdminUser;
function promoteAdmin(user: AuthOrgUser): AdminOrgUser;
function promoteAdmin(user: AuthUser | AuthOrgUser): AdminUser | AdminOrgUser {
  return { ...user, role: "admin" };
}

/**
 * Fetch organization details for a user
 */
async function fetchOrganizationDetails(
  userId: string,
  orgId?: string,
): Promise<OrganizationDetails | undefined> {
  if (orgId) {
    const org = await fetchOrganization(userId, orgId);
    if (org) {
      return org;
    }
  }
  return undefined;
}

/**
 * Fetch a specific organization by ID
 */
async function fetchOrganization(
  userId: string,
  orgId: string,
): Promise<OrganizationDetails | undefined> {
  const { data: org, error: orgError } = await supabasePrivileged
    .from(TABLES.ORGANIZATIONS)
    .select(
      `
      ${COLUMNS.ORGANIZATIONS.ID},
      ${COLUMNS.ORGANIZATIONS.NAME},
      ${COLUMNS.ORGANIZATIONS.CREATED_BY}
    `,
    )
    .eq(COLUMNS.ORGANIZATIONS.ID, orgId)
    .is(COLUMNS.ORGANIZATIONS.DELETED_AT, null)
    .single();

  if (orgError || !org) {
    return undefined;
  }

  if (org[COLUMNS.ORGANIZATIONS.CREATED_BY] === userId) {
    return {
      orgId: org[COLUMNS.ORGANIZATIONS.ID] as string,
      orgName: org[COLUMNS.ORGANIZATIONS.NAME] as string,
      orgRole: "admin",
    };
  }

  const { data: membership, error: membershipError } = await supabasePrivileged
    .from(TABLES.USERS_BY_ORG)
    .select(COLUMNS.USERS_BY_ORG.ROLE)
    .eq(COLUMNS.USERS_BY_ORG.USER_ID, userId)
    .eq(COLUMNS.USERS_BY_ORG.ORG_ID, orgId)
    .is(COLUMNS.USERS_BY_ORG.DELETED_AT, null)
    .single();

  if (membershipError || !membership) {
    return undefined;
  }

  const roleValue = membership[COLUMNS.USERS_BY_ORG.ROLE] as string;
  const orgRole: OrgRole = roleValue === "admin" ? "admin" : "member";

  return {
    orgId: org[COLUMNS.ORGANIZATIONS.ID] as string,
    orgName: org[COLUMNS.ORGANIZATIONS.NAME] as string,
    orgRole,
  };
}

/**
 * Authenticate a user via API key
 */
async function getUserByApiKey(
  token: string,
  host: string | null,
): Promise<OrgUser | User> {
  const { data: keyData, error: keyError } = await supabasePrivileged
    .from(TABLES.API_KEYS)
    .select(
      `
      ${COLUMNS.API_KEYS.USER_ID},
      ${COLUMNS.API_KEYS.NAME},
      ${COLUMNS.API_KEYS.API_KEY},
      ${COLUMNS.API_KEYS.DELETED_AT},
      ${COLUMNS.API_KEYS.ORG_ID}
    `,
    )
    .eq(COLUMNS.API_KEYS.API_KEY, token);

  if (keyError || !keyData) {
    console.warn(`auth: Error retrieving API keys => anon`, keyError);
    return makeAnonUser(host);
  }

  const activeKeys = keyData.filter((key) => !key[COLUMNS.API_KEYS.DELETED_AT]);
  if (activeKeys.length < 1) {
    console.log(`auth: API key not valid => anon`);
    return makeAnonUser(host);
  }

  const activeKey = activeKeys[0];
  const userId = activeKey[COLUMNS.API_KEYS.USER_ID];

  const { data: userData, error: userError } =
    await supabasePrivileged.auth.admin.getUserById(userId);
  if (userError || !userData) {
    console.warn(`auth: Error retrieving user data => anon`, userError);
    return makeAnonUser(host);
  }

  const orgId = activeKey[COLUMNS.API_KEYS.ORG_ID];
  const orgDetails = await fetchOrganizationDetails(userId, orgId);

  console.log(`auth: API key and user valid => user`);
  return makeNormalUser(
    userData.user,
    activeKey[COLUMNS.API_KEYS.NAME] as string,
    host,
    orgDetails,
  );
}

/**
 * Authenticate a user via JWT token
 */
async function getUserByJwt(
  token: string,
  host: string | null,
): Promise<OrgUser | User> {
  const supabase = await createServerClient();
  const { data, error } = await supabase.auth.getUser(token);
  if (error) {
    return makeAnonUser(host);
  }

  const orgDetails = await fetchOrganizationDetails(data.user.id);

  console.log(`auth: JWT token valid => user`);
  return makeNormalUser(data.user, DEFAULT_KEY_NAME, host, orgDetails);
}

/**
 * The token could be either a JWT or an API key, so try both
 * - Sometimes we pass in the JWT token as an API key
 * @param token
 * @param host
 * @returns
 */
async function getUserByAmbigiousToken(
  token: string,
  host: string | null,
): Promise<OrgUser | User> {
  const jwtUser = await getUserByJwt(token, host);
  const apiKeyUser =
    jwtUser.role === "anonymous" ? await getUserByApiKey(token, host) : jwtUser;

  const user =
    apiKeyUser.role === "anonymous"
      ? await verifyOsoJwt(token, host)
      : apiKeyUser;
  if (user.role === "anonymous") {
    return user;
  }

  const { data: adminData, error: adminError } = await supabasePrivileged
    .from(TABLES.ADMIN_USERS)
    .select(COLUMNS.ADMIN_USERS.USER_ID)
    .eq(COLUMNS.ADMIN_USERS.USER_ID, user.userId);

  if (adminError) {
    console.warn(`auth: Error retrieving admin users => user`, adminError);
    return user;
  }

  if (adminData && adminData.length > 0) {
    console.log(`auth: Valid key and admin => admin`);
    return promoteAdmin(user);
  }

  return user;
}

/**
 * Main function to authenticate a user from a request
 * - First tries to get user from HTTP header (Bearer token)
 * - If that fails, tries to get user from cookies (Supabase session)
 * If the user is not linked to an organization, returns anonymous user.
 * If you want to allow non-org users, use getUser() instead.
 * @param request
 * @returns
 */
async function getOrgUser(request: NextRequest): Promise<OrgUser> {
  const user = await getUserInternal(request);
  const maybeOrgUserSchema = OrgUserSchema.safeParse(user);
  if (!maybeOrgUserSchema.success) {
    return makeAnonUser(getHost(request));
  }

  return maybeOrgUserSchema.data;
}
/**
 * Main function to authenticate a user from a request
 * - First tries to get user from HTTP header (Bearer token)
 * - If that fails, tries to get user from cookies (Supabase session)
 * This may or may not contain organization details. If you require org details,
 * use getOrgUser() instead.
 * @param request
 * @returns
 */
async function getUser(request: NextRequest): Promise<User> {
  const user = await getUserInternal(request);
  const maybeUserSchema = UserSchema.safeParse(user);
  if (!maybeUserSchema.success) {
    return makeAnonUser(getHost(request));
  }

  return maybeUserSchema.data;
}

async function getUserInternal(request: NextRequest): Promise<OrgUser | User> {
  const userFromHttpHeader = await getUserByHttpHeader(request);
  if (userFromHttpHeader.role !== "anonymous") {
    return userFromHttpHeader;
  }
  const userFromCookies = await getUserByCookies(request);
  return userFromCookies;
}

/**
 * Tries to identify a user from the HTTP Authorization header
 * - Supports Bearer tokens that are either JWTs from Supabase or API keys
 * @param request
 * @returns
 */
async function getUserByHttpHeader(
  request: NextRequest,
): Promise<OrgUser | User> {
  const headers = request.headers;
  const host = getHost(request);
  const auth = headers.get("authorization");

  if (!auth) {
    console.log(`auth: No token => anon`);
    return makeAnonUser(host);
  }

  // Remove "Bearer " prefix if it exists
  const trimmedAuth = auth.trim();
  const token = trimmedAuth.toLowerCase().startsWith(AUTH_PREFIX)
    ? trimmedAuth.slice(AUTH_PREFIX.length).trim()
    : trimmedAuth;

  return await getUserByAmbigiousToken(token, host);
}

/**
 * Tries to identify a user from cookies (Supabase session)
 * @param request
 * @returns
 */
async function getUserByCookies(request: NextRequest): Promise<OrgUser | User> {
  const host = getHost(request);
  const supabase = await createServerClient();
  const { data, error } = await supabase.auth.getSession();
  const token = data?.session?.access_token;

  if (error || !token) {
    console.log("getUserByCookies: No valid session => anon", error);
    return makeAnonUser(null);
  }
  return await getUserByAmbigiousToken(token, host);
}

async function signOsoJwt(
  user: AuthOrgUser | AuthUser,
  org: Omit<OrganizationDetails, "orgRole">,
  expirationTime: string = "1h",
): Promise<string> {
  const secret = OSO_JWT_SECRET;
  if (!secret) {
    throw new Error("JWT Secret not found: unable to authenticate");
  }

  const authUser: AuthOrgUser = {
    ...user,
    ...org,
    role: "user",
    orgRole: "member",
  }; // For JWT requests, default to lower permissions for now

  return new SignJWT(authUser as any)
    .setProtectedHeader({ alg: "HS256" })
    .setAudience("opensource-observer")
    .setIssuer("opensource-observer")
    .setExpirationTime(expirationTime)
    .sign(new TextEncoder().encode(secret));
}

async function verifyOsoJwt(
  token: string,
  host: string | null,
): Promise<AuthOrgUser | AnonUser> {
  const secret = OSO_JWT_SECRET;
  if (!secret) {
    throw new Error("JWT Secret not found: unable to authenticate");
  }
  try {
    const { payload } = await jwtVerify<AuthOrgUser>(
      token,
      new TextEncoder().encode(secret),
      {
        algorithms: ["HS256"],
        audience: "opensource-observer",
        issuer: "opensource-observer",
      },
    );

    return AuthOrgUserSchema.parse(payload);
  } catch (e: unknown) {
    console.log(
      `auth: Invalid JWT token: ${e instanceof Error ? e.message : ""} => anon`,
    );
    return makeAnonUser(host);
  }
}

/**
 * Gets the host from the request
 */
function getHost(req: NextRequest) {
  const host = req.headers.get("host");
  const forwardedHost = req.headers.get("x-forwarded-host");
  return forwardedHost ?? host;
}

async function setSupabaseSession(
  supabaseClient: SupabaseClient<Database>,
  request: NextRequest,
) {
  const authHeader = request.headers.get("X-Supabase-Auth")?.split(":");
  if (!authHeader || authHeader.length !== 2) {
    return { error: "Invalid header" };
  }
  const [accessToken, refreshToken] = authHeader;
  const { data, error } = await supabaseClient.auth.setSession({
    access_token: accessToken,
    refresh_token: refreshToken,
  });
  if (error) {
    return { error: error.message };
  }
  return { data, error: null };
}

export { getOrgUser, getUser, setSupabaseSession, signOsoJwt, verifyOsoJwt };
