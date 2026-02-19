import {
  createAdminClient,
  type SupabaseAdminClient,
} from "@/lib/supabase/admin";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { requireAuthentication } from "@/app/api/v1/osograph/utils/auth";
import { AuthenticationErrors } from "@/app/api/v1/osograph/utils/errors";
import { getUserOrganizationIds } from "@/app/api/v1/osograph/utils/resolver-helpers";
import type { Database } from "@/lib/types/supabase";
import { logger } from "@/lib/logger";

/**
 * Describes the org-scoping behavior of the current authentication context.
 * - api_token: Restricted to a single org (from api_keys.org_id)
 * - pat: Supabase JWT login, can access all user orgs
 * - system: Internal system credentials
 */
export type OrgScope =
  | { type: "api_token"; orgId: string }
  | { type: "pat" }
  | { type: "system" };

/**
 * Determines the org scope from the current GraphQL context.
 * API tokens are restricted to their associated org.
 * PATs can access all user orgs.
 */
export function getOrgScope(context: GraphQLContext): OrgScope {
  if (context.systemCredentials) {
    return { type: "system" };
  }
  const { user } = context;
  if (
    user.role !== "anonymous" &&
    user.keyName !== "login" &&
    "orgId" in user &&
    user.orgId
  ) {
    return { type: "api_token", orgId: user.orgId };
  }
  return { type: "pat" };
}

/**
 * Table names from Supabase schema.
 */
type Tables = Database["public"]["Tables"] & Database["public"]["Views"];

/**
 * Extract column names from a table's Row type.
 */
type TableColumns<T extends keyof Tables> = keyof Tables[T]["Row"] & string;

/**
 * Valid column names for resource_permissions table that reference resources.
 * These are the foreign key columns (notebook_id, chat_id, etc.)
 */
type ResourcePermissionColumn = TableColumns<"resource_permissions">;

/**
 * Resource types that support permission-based access control.
 * Supports notebooks, chats, datasets, data models, static models,
 * data ingestions, and data connections.
 */
export type ResourceType =
  | "notebook"
  | "chat"
  | "dataset"
  | "data_model"
  | "static_model"
  | "data_ingestion"
  | "data_connection";

/**
 * Permission levels in hierarchical order (highest to lowest).
 * - owner: Full control, can delete and manage all permissions
 * - admin: Can manage permissions for users with lower levels
 * - write: Can modify the resource
 * - read: Can view the resource
 * - none: No access
 */
export type PermissionLevel = "none" | "read" | "write" | "admin" | "owner";

/**
 * Organization role from users_by_organization.user_role
 * - owner: Full control over org and all resources
 * - admin: Can manage org members and has full access to resources
 * - member: Standard org member with read access by default
 */
export type OrgRole = "owner" | "admin" | "member";

/**
 * Result returned by getOrgScopedClient containing both the client and
 * the user's role in the organization.
 */
export interface OrgAccessResult {
  client: SupabaseAdminClient;
  orgRole: OrgRole;
  userId: string;
}

/**
 * Result returned by getOrgResourceClient containing both the client and
 * the actual permission level the user has on the resource.
 */
export interface ResourceAccessResult {
  client: SupabaseAdminClient;
  permissionLevel: Exclude<PermissionLevel, "none">;
}

/**
 * Permission level hierarchy for comparison.
 * Higher number = higher permission level.
 */
const PERMISSION_HIERARCHY: Record<PermissionLevel, number> = {
  none: 0,
  read: 1,
  write: 2,
  admin: 3,
  owner: 4,
};

/**
 * Checks if the user's permission level meets the required minimum.
 */
function hasMinimumPermission(
  userLevel: PermissionLevel,
  requiredLevel: PermissionLevel,
): boolean {
  return PERMISSION_HIERARCHY[userLevel] >= PERMISSION_HIERARCHY[requiredLevel];
}

/**
 * Checks if an org role should bypass resource permission overrides.
 * Owner and admin roles have full access regardless of resource_permissions.
 */
function bypassesResourcePermissions(orgRole: OrgRole): boolean {
  return orgRole === "owner" || orgRole === "admin";
}

/**
 * Validates that a permission level meets the required minimum and returns
 * the ResourceAccessResult, or throws an authorization error.
 *
 * @param permissionLevel User's actual permission level
 * @param requiredPermission Minimum permission level needed
 * @returns ResourceAccessResult with admin client and permission level
 * @throws {AuthenticationErrors.notAuthorized()} if permission is insufficient
 */
function validateAndReturnResourceAccess(
  permissionLevel: PermissionLevel,
  requiredPermission: PermissionLevel,
): ResourceAccessResult {
  if (hasMinimumPermission(permissionLevel, requiredPermission)) {
    return {
      client: createAdminClient(),
      permissionLevel: permissionLevel as Exclude<PermissionLevel, "none">,
    };
  }
  logger.error("Permission level insufficient", {
    permissionLevel,
    requiredPermission,
  });
  throw AuthenticationErrors.notAuthorized();
}

/**
 * Get a Supabase admin client for system-level operations.
 * Validates that systemCredentials are present in the context.
 *
 * This should only be used in resolvers/system/ directory for internal
 * operations like scheduler tasks that bypass user authentication.
 *
 * @param context GraphQL context
 * @returns Supabase admin client
 * @throws {AuthenticationErrors.notAuthorized()} if systemCredentials missing
 */
export function getSystemClient(context: GraphQLContext): SupabaseAdminClient {
  if (!context.systemCredentials) {
    logger.error("System credentials missing in context");
    throw AuthenticationErrors.notAuthorized();
  }
  return createAdminClient();
}

/**
 * Returns the user's organization IDs, using the request-scoped cache
 */
async function getOrCacheUserOrgIds(
  context: GraphQLContext,
  userId: string,
  client: SupabaseAdminClient,
): Promise<string[]> {
  const cached = context.authCache.orgIds.get(userId);
  if (cached) return cached;

  const orgIds = await getUserOrganizationIds(userId, client);
  context.authCache.orgIds.set(userId, orgIds);
  return orgIds;
}

/**
 * Result returned by getAuthenticatedClient containing the client,
 * user's ID, and org IDs scoped by token type.
 */
export interface AuthenticatedClientResult {
  client: SupabaseAdminClient;
  userId: string;
  orgIds: string[];
  orgScope: OrgScope;
}

/**
 * Get a Supabase admin client for authenticated user operations.
 * Validates that the user is authenticated (not anonymous).
 * Returns orgIds already scoped by token type:
 * - API tokens → [tokenOrgId]
 * - PATs → all user orgs
 *
 * Note: This does NOT check org membership, use getOrgScopedClient for that.
 *
 * @param context GraphQL context
 * @returns Object containing Supabase admin client, user ID, scoped orgIds, and orgScope
 * @throws {AuthenticationErrors.notAuthenticated()} if user is anonymous
 */
export async function getAuthenticatedClient(
  context: GraphQLContext,
): Promise<AuthenticatedClientResult> {
  const user = requireAuthentication(context.user);
  const client = createAdminClient();
  const orgScope = getOrgScope(context);
  const orgIds =
    orgScope.type === "api_token"
      ? [orgScope.orgId]
      : await getOrCacheUserOrgIds(context, user.userId, client);

  return { client, userId: user.userId, orgIds, orgScope };
}

/**
 * Get a Supabase admin client for operations scoped to an organization.
 * Validates user is authenticated AND is a member of the specified org.
 * Returns both the client and the user's role in the organization.
 *
 * This is the most common helper for authenticated resolvers that work with
 * org-specific resources like datasets, notebooks, etc.
 *
 * @param context GraphQL context
 * @param orgId Organization ID to check membership
 * @returns Object containing Supabase admin client and user's org role
 * @throws {AuthenticationErrors.notAuthenticated()} if user is anonymous
 * @throws {AuthenticationErrors.notAuthorized()} if user is not an org member
 */
export async function getOrgScopedClient(
  context: GraphQLContext,
  orgId: string,
): Promise<OrgAccessResult> {
  const user = requireAuthentication(context.user);

  const orgScope = getOrgScope(context);
  if (orgScope.type === "api_token" && orgScope.orgId !== orgId) {
    logger.error("API token cross-org access denied", {
      tokenOrgId: orgScope.orgId,
      requestedOrgId: orgId,
    });
    throw AuthenticationErrors.notAuthorized();
  }

  const client = createAdminClient();
  const orgRole = await getOrgRoleCached(client, context, user.userId, orgId);

  if (!orgRole) {
    logger.error("User is not a member of organization", {
      userId: user.userId,
      orgId,
    });
    throw AuthenticationErrors.notAuthorized();
  }

  return { client, orgRole, userId: user.userId };
}

/**
 * Configuration for a resource type, mapping it to:
 * - The database table where the resource lives
 * - The column in resource_permissions that references this resource
 */
export interface ResourceConfig<T extends keyof Tables> {
  table: T;
  permissionColumn: ResourcePermissionColumn;
}

/**
 * Maps resource types to their corresponding database table and column names.
 * Type-safe: permissionColumn must be a valid column in resource_permissions.
 */
export const RESOURCE_CONFIG: {
  notebook: ResourceConfig<"notebooks">;
  chat: ResourceConfig<"chat_history">;
  dataset: ResourceConfig<"datasets">;
  data_model: ResourceConfig<"model">;
  static_model: ResourceConfig<"static_model">;
  data_ingestion: ResourceConfig<"data_ingestions">;
  data_connection: ResourceConfig<"dynamic_connectors">;
} = {
  notebook: { table: "notebooks", permissionColumn: "notebook_id" },
  chat: { table: "chat_history", permissionColumn: "chat_id" },
  dataset: { table: "datasets", permissionColumn: "dataset_id" },
  data_model: { table: "model", permissionColumn: "data_model_id" },
  static_model: { table: "static_model", permissionColumn: "static_model_id" },
  data_ingestion: {
    table: "data_ingestions",
    permissionColumn: "data_ingestion_id",
  },
  data_connection: {
    table: "dynamic_connectors",
    permissionColumn: "data_connection_id",
  },
};

/**
 * Helper function to get org role with caching.
 */
async function getOrgRoleCached(
  client: SupabaseAdminClient,
  context: GraphQLContext,
  userId: string,
  orgId: string,
): Promise<OrgRole | undefined> {
  const cacheKey = `${userId}:${orgId}`;
  const cached = context.authCache.orgMemberships.get(cacheKey) as
    | OrgRole
    | undefined;
  if (cached) return cached;

  const { data: membership } = await client
    .from("users_by_organization")
    .select("user_role")
    .eq("user_id", userId)
    .eq("org_id", orgId)
    .is("deleted_at", null)
    .single();

  if (!membership) return undefined;

  const role = membership.user_role as OrgRole;
  context.authCache.orgMemberships.set(cacheKey, role);
  return role;
}

/**
 * Get a Supabase admin client for operations on a resource within an organization.
 * Validates user is authenticated AND has access through EITHER:
 * 1. Org membership (users_by_organization) → the source of truth
 * 2. Resource permissions (resource_permissions) → overrides for members
 *
 * Permission Resolution Order:
 * 1. Check user's org membership role:
 *    - owner/admin → full access (bypasses resource_permissions)
 *    - member → default "read", can be overridden by resource_permissions
 *    - no membership → continue to step 2
 * 2. Check resource_permissions for user-specific override
 * 3. If user is org member, grant default "read" access
 * 4. Check resource_permissions for public permission
 * 5. Deny access
 *
 * @param context GraphQL context
 * @param resourceType Type of resource (notebook, chat, etc.)
 * @param resourceId ID of the specific resource
 * @param requiredPermission Minimum permission level needed (defaults to "read")
 * @returns Object containing the admin client and the user's effective permission level
 * @throws {AuthenticationErrors.notAuthenticated()} if user is anonymous
 * @throws {AuthenticationErrors.notAuthorized()} if user lacks required permission
 *
 * @example
 * ```typescript
 * // In resolvers/resource/notebook.ts (flat structure)
 * const { client, permissionLevel } = await getOrgResourceClient(
 *   context,
 *   "notebook",
 *   args.notebookId,
 *   "write"
 * );
 * ```
 */
export async function getOrgResourceClient(
  context: GraphQLContext,
  resourceType: ResourceType,
  resourceId: string,
  requiredPermission: Exclude<PermissionLevel, "none"> = "read",
): Promise<ResourceAccessResult> {
  const user = requireAuthentication(context.user);
  const cacheKey = `${user.userId}:${resourceType}:${resourceId}`;

  const cachedPermission = context.authCache.resourcePermissions.get(cacheKey);
  if (cachedPermission) {
    return validateAndReturnResourceAccess(
      cachedPermission as PermissionLevel,
      requiredPermission,
    );
  }

  const client = createAdminClient();
  const config = RESOURCE_CONFIG[resourceType];

  const { data: resource } = await client
    .from(config.table)
    .select("org_id")
    .eq("id", resourceId)
    .is("deleted_at", null)
    .single();

  if (!resource) {
    logger.error("Resource not found", { resourceType, resourceId });
    throw AuthenticationErrors.notAuthorized();
  }

  const orgScope = getOrgScope(context);
  const isCrossOrgApiToken =
    orgScope.type === "api_token" && orgScope.orgId !== resource.org_id;

  const orgRole = isCrossOrgApiToken
    ? undefined
    : await getOrgRoleCached(client, context, user.userId, resource.org_id);

  if (orgRole && bypassesResourcePermissions(orgRole)) {
    const permissionLevel = orgRole === "owner" ? "owner" : "admin";
    context.authCache.resourcePermissions.set(cacheKey, permissionLevel);
    return { client, permissionLevel };
  }

  if (!isCrossOrgApiToken) {
    const { data: userPermission } = await client
      .from("resource_permissions")
      .select("permission_level")
      .eq("user_id", user.userId)
      .eq(config.permissionColumn, resourceId)
      .is("revoked_at", null)
      .single();

    if (userPermission) {
      const userLevel = userPermission.permission_level as PermissionLevel;
      context.authCache.resourcePermissions.set(cacheKey, userLevel);
      return validateAndReturnResourceAccess(userLevel, requiredPermission);
    }
  }

  if (orgRole === "member") {
    context.authCache.resourcePermissions.set(cacheKey, "read");
    return validateAndReturnResourceAccess("read", requiredPermission);
  }

  const publicPermission = await getResourcePublicPermission(
    resourceId,
    resourceType,
    client,
  );

  context.authCache.resourcePermissions.set(cacheKey, publicPermission);
  return validateAndReturnResourceAccess(publicPermission, requiredPermission);
}

export async function getResourcePublicPermission(
  resourceId: string,
  resourceType: ResourceType,
  adminClient: SupabaseAdminClient,
): Promise<PermissionLevel> {
  const config = RESOURCE_CONFIG[resourceType];
  const { data: publicPermission } = await adminClient
    .from("resource_permissions")
    .select("permission_level")
    .is("org_id", null)
    .is("user_id", null)
    .eq(config.permissionColumn, resourceId)
    .is("revoked_at", null)
    .maybeSingle();

  return publicPermission
    ? (publicPermission.permission_level as PermissionLevel)
    : "none";
}
