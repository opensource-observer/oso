import "server-only";
import { type NextRequest } from "next/server";
import {
  createPrivilegedSupabaseClient,
  createNormalSupabaseClient,
} from "@/lib/clients/supabase";
import { SupabaseClient, User as SupabaseUser } from "@supabase/supabase-js";
import {
  AnonUser,
  NormalUser,
  AdminUser,
  AuthUser,
  User,
  OrganizationDetails,
  OrgRole,
} from "@/lib/types/user";
import { Database } from "@/lib/types/supabase";

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

const supabasePrivileged = createPrivilegedSupabaseClient();

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
  orgDetails?: OrganizationDetails,
): NormalUser => {
  const normalUser: NormalUser = {
    role: "user",
    host,
    userId: user.id,
    keyName,
    email: user.email,
    name: user.user_metadata.name,
  };

  if (orgDetails) {
    normalUser.orgId = orgDetails.orgId;
    normalUser.orgName = orgDetails.orgName;
    normalUser.orgRole = orgDetails.orgRole;
  }

  return normalUser;
};

/**
 * Promote a user to admin role
 */
const promoteAdmin = (user: AuthUser): AdminUser => ({
  ...user,
  role: "admin",
});

/**
 * Fetch organization details for a user
 */
async function fetchOrganizationDetails(
  userId: string,
  orgId?: string,
): Promise<OrganizationDetails | undefined> {
  if (orgId) {
    return fetchSpecificOrganization(userId, orgId);
  }

  return fetchPrimaryOrganization(userId);
}

/**
 * Fetch a specific organization by ID
 */
async function fetchSpecificOrganization(
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
 * Fetch the primary organization for a user
 */
async function fetchPrimaryOrganization(
  userId: string,
): Promise<OrganizationDetails | undefined> {
  const { data: createdOrg, error: createdOrgError } = await supabasePrivileged
    .from(TABLES.ORGANIZATIONS)
    .select(
      `
      ${COLUMNS.ORGANIZATIONS.ID},
      ${COLUMNS.ORGANIZATIONS.NAME}
    `,
    )
    .eq(COLUMNS.ORGANIZATIONS.CREATED_BY, userId)
    .order("created_at", { ascending: false })
    .limit(1)
    .single();

  if (!createdOrgError && createdOrg) {
    return {
      orgId: createdOrg[COLUMNS.ORGANIZATIONS.ID] as string,
      orgName: createdOrg[COLUMNS.ORGANIZATIONS.NAME] as string,
      orgRole: "admin",
    };
  }

  const { data: membership, error: membershipError } = await supabasePrivileged
    .from(TABLES.USERS_BY_ORG)
    .select(
      `
      ${COLUMNS.USERS_BY_ORG.ROLE},
      organizations (
        ${COLUMNS.ORGANIZATIONS.ID},
        ${COLUMNS.ORGANIZATIONS.NAME}
      )
    `,
    )
    .eq(COLUMNS.USERS_BY_ORG.USER_ID, userId)
    .is(COLUMNS.USERS_BY_ORG.DELETED_AT, null)
    .order("created_at", { ascending: false })
    .limit(1)
    .single();

  if (membershipError || !membership || !membership.organizations) {
    return undefined;
  }

  const roleValue = membership[COLUMNS.USERS_BY_ORG.ROLE] as string;
  const orgRole: OrgRole = roleValue === "admin" ? "admin" : "member";

  return {
    orgId: membership.organizations[COLUMNS.ORGANIZATIONS.ID] as string,
    orgName: membership.organizations[COLUMNS.ORGANIZATIONS.NAME] as string,
    orgRole,
  };
}

/**
 * Authenticate a user via API key
 */
async function getUserByApiKey(
  token: string,
  host: string | null,
): Promise<User> {
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
  const userId = activeKey[COLUMNS.API_KEYS.USER_ID] as string;

  const { data: userData, error: userError } =
    await supabasePrivileged.auth.admin.getUserById(userId);
  if (userError || !userData) {
    console.warn(`auth: Error retrieving user data => anon`, userError);
    return makeAnonUser(host);
  }

  const orgId = activeKey[COLUMNS.API_KEYS.ORG_ID] as string | undefined;
  const orgDetails = orgId
    ? await fetchOrganizationDetails(userId, orgId).catch(() => undefined)
    : undefined;

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
async function getUserByJwt(token: string, host: string | null): Promise<User> {
  const { data, error } =
    await createNormalSupabaseClient().auth.getUser(token);
  if (error) {
    return makeAnonUser(host);
  }

  const orgDetails = await fetchOrganizationDetails(data.user.id).catch(
    () => undefined,
  );

  console.log(`auth: JWT token valid => user`);
  return makeNormalUser(data.user, DEFAULT_KEY_NAME, host, orgDetails);
}

/**
 * Main function to authenticate a user from a request
 */
async function getUser(request: NextRequest): Promise<User> {
  const headers = request.headers;
  const host = getHost(request);
  const auth = headers.get("authorization");

  if (!auth) {
    console.log(`auth: No token => anon`);
    return makeAnonUser(host);
  }

  const trimmedAuth = auth.trim();
  const token = trimmedAuth.toLowerCase().startsWith(AUTH_PREFIX)
    ? trimmedAuth.slice(AUTH_PREFIX.length).trim()
    : trimmedAuth;

  const jwtUser = await getUserByJwt(token, host);
  const user =
    jwtUser.role === "anonymous" ? await getUserByApiKey(token, host) : jwtUser;

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

export { getUser, setSupabaseSession };
