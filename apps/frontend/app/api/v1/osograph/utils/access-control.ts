import {
  createAdminClient,
  type SupabaseAdminClient,
} from "@/lib/supabase/admin";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import { requireAuthentication } from "@/app/api/v1/osograph/utils/auth";
import { AuthenticationErrors } from "@/app/api/v1/osograph/utils/errors";
import type { Database } from "@/lib/types/supabase";
import { logger } from "@/lib/logger";

/**
 * Table names from Supabase schema.
 */
type Tables = Database["public"]["Tables"];

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
 * Result returned by getAuthenticatedClient containing both the client and
 * the user's ID.
 */
export interface AuthenticatedClientResult {
  client: SupabaseAdminClient;
  userId: string;
}

/**
 * Get a Supabase admin client for authenticated user operations.
 * Validates that the user is authenticated (not anonymous).
 *
 * Note: This does NOT check org membership, use getOrgScopedClient for that.
 * This is useful for user profile operations.
 *
 * @param context GraphQL context
 * @returns Object containing Supabase admin client and user ID
 * @throws {AuthenticationErrors.notAuthenticated()} if user is anonymous
 */
export function getAuthenticatedClient(
  context: GraphQLContext,
): AuthenticatedClientResult {
  const user = requireAuthentication(context.user);
  return {
    client: createAdminClient(),
    userId: user.userId,
  };
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
  const cacheKey = `${user.userId}:${orgId}`;

  const cachedRole = context.authCache.orgMemberships.get(cacheKey);
  if (cachedRole) {
    return {
      client: createAdminClient(),
      orgRole: cachedRole as OrgRole,
      userId: user.userId,
    };
  }

  const client = createAdminClient();
  const { data: membership } = await client
    .from("users_by_organization")
    .select("user_role")
    .eq("user_id", user.userId)
    .eq("org_id", orgId)
    .is("deleted_at", null)
    .single();

  if (!membership) {
    logger.error("User is not a member of organization", {
      userId: user.userId,
      orgId,
    });
    throw AuthenticationErrors.notAuthorized();
  }

  const orgRole = membership.user_role as OrgRole;
  context.authCache.orgMemberships.set(cacheKey, orgRole);

  return { client, orgRole, userId: user.userId };
}

/**
 * Configuration for a resource type, mapping it to:
 * - The database table where the resource lives
 * - The column in resource_permissions that references this resource
 */
interface ResourceConfig<T extends keyof Tables> {
  table: T;
  permissionColumn: ResourcePermissionColumn;
}

/**
 * Maps resource types to their corresponding database table and column names.
 * Type-safe: permissionColumn must be a valid column in resource_permissions.
 */
const RESOURCE_CONFIG: {
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

  // Check orgMemberships cache before querying DB
  const membershipCacheKey = `${user.userId}:${resource.org_id}`;
  let orgRole = context.authCache.orgMemberships.get(membershipCacheKey) as
    | OrgRole
    | undefined;

  if (!orgRole) {
    const { data: membership } = await client
      .from("users_by_organization")
      .select("user_role")
      .eq("user_id", user.userId)
      .eq("org_id", resource.org_id)
      .is("deleted_at", null)
      .single();

    if (membership) {
      orgRole = membership.user_role as OrgRole;
      context.authCache.orgMemberships.set(membershipCacheKey, orgRole);
    }
  }

  if (orgRole && bypassesResourcePermissions(orgRole)) {
    const permissionLevel = orgRole === "owner" ? "owner" : "admin";
    context.authCache.resourcePermissions.set(cacheKey, permissionLevel);
    return { client, permissionLevel };
  }

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

  if (orgRole === "member") {
    context.authCache.resourcePermissions.set(cacheKey, "read");
    return validateAndReturnResourceAccess("read", requiredPermission);
  }

  const { data: publicPermission } = await client
    .from("resource_permissions")
    .select("permission_level")
    .is("user_id", null)
    .eq(config.permissionColumn, resourceId)
    .is("revoked_at", null)
    .single();

  if (publicPermission) {
    const publicLevel = publicPermission.permission_level as PermissionLevel;
    context.authCache.resourcePermissions.set(cacheKey, publicLevel);
    return validateAndReturnResourceAccess(publicLevel, requiredPermission);
  }

  logger.error("User lacks permission to access resource", {
    userId: user.userId,
    resourceType,
    resourceId,
  });
  throw AuthenticationErrors.notAuthorized();
}
