/**
 * Enhanced context types with branded types for compile-time tracking of middleware application.
 *
 * These types use TypeScript's branded types pattern to ensure that resolver handlers
 * can only access certain context properties (like `client`, `userId`, `orgRole`) if the
 * appropriate middleware/enhancer has been applied through the resolver builder.
 *
 * Example:
 * ```typescript
 * createResolver<SomePayload>()
 *   .use(requireAuth())  // adds AuthenticatedContext properties
 *   .resolve((parent, args, context) => {
 *     // TypeScript knows context.client and context.userId exist
 *   });
 * ```
 */

import type { SupabaseAdminClient } from "@/lib/supabase/admin";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import type {
  OrgRole,
  PermissionLevel,
} from "@/app/api/v1/osograph/utils/access-control";

// Branded type markers (unique symbols for compile-time tracking)
declare const AuthenticatedBrand: unique symbol;
declare const OrgAccessBrand: unique symbol;
declare const ResourceAccessBrand: unique symbol;

/**
 * Enhanced context type after authentication middleware.
 *
 * Guarantees that:
 * - User is authenticated (not anonymous)
 * - `client` is a Supabase admin client
 * - `userId` is available
 *
 * Applied by: `requireAuth()` enhancer
 */
export type AuthenticatedContext = GraphQLContext & {
  [AuthenticatedBrand]: true;
  client: SupabaseAdminClient;
  userId: string;
};

/**
 * Enhanced context type after organization access middleware.
 *
 * Guarantees that:
 * - User is authenticated
 * - User is a member of the specified organization
 * - `client` is available
 * - `orgRole` indicates the user's role in the organization
 * - `orgId` is the organization being accessed
 *
 * Applied by: `requireOrgAccess()` enhancer
 *
 * @template T - Optional type parameter to track args type for type inference
 */
export type OrgAccessContext<T = unknown> = AuthenticatedContext & {
  [OrgAccessBrand]: true;
  orgRole: OrgRole;
  orgId: string;
  _orgAccessArgs?: T; // Used for type inference, not runtime value
};

/**
 * Enhanced context type after resource access middleware.
 *
 * Guarantees that:
 * - User is authenticated
 * - User has the required permission level on the resource
 * - `client` is available
 * - `permissionLevel` indicates the user's permission (excluding 'none')
 * - `resourceId` is the resource being accessed
 *
 * Applied by: `requireResourceAccess()` enhancer
 */
export type ResourceAccessContext = AuthenticatedContext & {
  [ResourceAccessBrand]: true;
  permissionLevel: Exclude<PermissionLevel, "none">;
  resourceId: string;
};
