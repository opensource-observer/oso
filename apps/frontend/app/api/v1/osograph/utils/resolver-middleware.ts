/**
 * Pre-built middleware library for common resolver patterns.
 *
 * This module provides factory functions that create middleware for:
 * - Access-control (4 tiers: org-scoped, authenticated, resource-scoped, system)
 * - Input validation
 * - Logging and monitoring
 *
 * Each middleware progressively enhances the context and/or args types,
 * providing compile-time type safety.
 *
 * Example usage:
 * ```typescript
 * export const createDataset = createResolver<CreateDatasetPayload>()
 *   .use(withValidation(CreateDatasetSchema))
 *   .use(withOrgScopedClient(({ args }) => args.input.orgId))
 *   .use(withLogging('createDataset'))
 *   .resolve(async (parent, args, context) => {
 *     // Implementation
 *   });
 * ```
 */

import { z } from "zod";
import { validateInput } from "@/app/api/v1/osograph/utils/validation";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import type {
  OrgScopedContext,
  AuthenticatedClientContext,
  ResourceScopedContext,
  SystemContext,
} from "@/app/api/v1/osograph/types/enhanced-context";
import type { Middleware } from "@/app/api/v1/osograph/utils/resolver-builder";
import {
  getOrgScopedClient,
  getAuthenticatedClient,
  getOrgResourceClient,
  getSystemClient,
  type ResourceType,
  type PermissionLevel,
} from "@/app/api/v1/osograph/utils/access-control";
import { requireAuthentication } from "@/app/api/v1/osograph/utils/auth";

/**
 * Org-scoped middleware — validates that the user is authenticated and a member of the org.
 *
 * Enhances the context with:
 * - `client`: Supabase admin client
 * - `orgId`: The organization being accessed
 * - `orgRole`: The user's role in the org (`"owner" | "admin" | "member"`)
 * - `userId`: The authenticated user's ID
 * - `authenticatedUser`: The authenticated user object
 *
 * Throws an authentication error if the user is not logged in.
 * Throws an authorization error if the user is not a member of the org.
 *
 * @template TArgs - The args type (passed through unchanged)
 * @param getOrgId - Extracts the org ID from context and args
 * @returns Middleware that transitions `GraphQLContext` → `OrgScopedContext`
 *
 * @example
 * ```typescript
 * createResolver<CreateNotebookPayload>()
 *   .use(withValidation(CreateNotebookInputSchema()))
 *   .use(withOrgScopedClient(({ args }) => args.input.orgId))
 *   .resolve(async (_, { input }, context) => {
 *     // context.client, context.orgId, context.orgRole, context.userId are now available
 *   });
 * ```
 */
export function withOrgScopedClient<TParent, TArgs>(
  getOrgId: (opts: {
    parent: TParent;
    context: GraphQLContext;
    args: TArgs;
  }) => string,
): Middleware<TParent, GraphQLContext, OrgScopedContext, TArgs, TArgs> {
  return async (parent, context, args) => {
    const orgId = getOrgId({ parent, context, args });
    const { client, orgRole, userId } = await getOrgScopedClient(
      context,
      orgId,
    );
    const authenticatedUser = requireAuthentication(context.user);

    const enhancedContext: OrgScopedContext = {
      ...context,
      client,
      orgId,
      orgRole,
      userId,
      authenticatedUser,
    } as OrgScopedContext;

    return { context: enhancedContext, args };
  };
}

/**
 * Authenticated client middleware — validates that the user is authenticated.
 *
 * Enhances the context with:
 * - `client`: Supabase admin client
 * - `userId`: The authenticated user's ID
 * - `orgIds`: Org IDs scoped by token type (API token → [tokenOrgId], PAT → all user orgs)
 * - `orgScope`: Describes the authentication scope
 * - `authenticatedUser`: The authenticated user object
 *
 * Throws an authentication error if the user is not logged in.
 *
 * @template TArgs - The args type (passed through unchanged)
 * @returns Middleware that transitions `GraphQLContext` → `AuthenticatedClientContext`
 *
 * @example
 * ```typescript
 * createResolver<ViewerPayload>()
 *   .use(withAuthenticatedClient())
 *   .resolve(async (_, args, context) => {
 *     // context.client and context.userId are now available
 *   });
 * ```
 */
export function withAuthenticatedClient<
  TParent = unknown,
  TArgs = unknown,
>(): Middleware<
  TParent,
  GraphQLContext,
  AuthenticatedClientContext,
  TArgs,
  TArgs
> {
  return async (parent, context, args) => {
    const { client, userId, orgIds, orgScope } =
      await getAuthenticatedClient(context);
    const authenticatedUser = requireAuthentication(context.user);

    const enhancedContext: AuthenticatedClientContext = {
      ...context,
      client,
      userId,
      orgIds,
      orgScope,
      authenticatedUser,
    } as AuthenticatedClientContext;

    return { context: enhancedContext, args };
  };
}

/**
 * Resource-scoped middleware — validates that the user has the required permission on a resource.
 *
 * Enhances the context with:
 * - `client`: Supabase admin client
 * - `permissionLevel`: The user's effective permission on the resource (excluding `"none"`)
 * - `resourceId`: The resource being accessed
 * - `authenticatedUser`: The authenticated user object
 *
 * Throws an authentication error if the user is not logged in.
 * Throws an authorization error if the user lacks the required permission.
 *
 * @template TArgs - The args type (passed through unchanged)
 * @param resourceType - The type of resource (e.g., `"data_model"`, `"notebook"`)
 * @param getResourceId - Extracts the resource ID from context and args
 * @param requiredPermission - Minimum permission level required (defaults to `"read"`)
 * @returns Middleware that transitions `GraphQLContext` → `ResourceScopedContext`
 *
 * @example
 * ```typescript
 * createResolver<UpdateDataModelPayload>()
 *   .use(withValidation(UpdateDataModelInputSchema()))
 *   .use(withOrgResourceClient("data_model", ({ args }) => args.input.dataModelId, "write"))
 *   .resolve(async (_, { input }, context) => {
 *     // context.client, context.permissionLevel, context.resourceId are now available
 *   });
 * ```
 */
export function withOrgResourceClient<TParent, TArgs>(
  resourceType: ResourceType,
  getResourceId: (opts: {
    parent: TParent;
    context: GraphQLContext;
    args: TArgs;
  }) => string,
  requiredPermission?: Exclude<PermissionLevel, "none">,
): Middleware<TParent, GraphQLContext, ResourceScopedContext, TArgs, TArgs> {
  return async (parent, context, args) => {
    const resourceId = getResourceId({ parent, context, args });
    const { client, permissionLevel } = await getOrgResourceClient(
      context,
      resourceType,
      resourceId,
      requiredPermission,
    );
    const authenticatedUser = requireAuthentication(context.user);

    const enhancedContext: ResourceScopedContext = {
      ...context,
      client,
      permissionLevel,
      resourceId,
      authenticatedUser,
    } as ResourceScopedContext;

    return { context: enhancedContext, args };
  };
}

/**
 * System client middleware — validates that system credentials are present.
 *
 * Enhances the context with:
 * - `client`: Supabase admin client
 *
 * Throws an authorization error if system credentials are missing.
 *
 * @template TArgs - The args type (passed through unchanged)
 * @returns Middleware that transitions `GraphQLContext` → `SystemContext`
 *
 * @example
 * ```typescript
 * createResolver<RunScheduledJobPayload>()
 *   .use(withSystemClient())
 *   .resolve((_, args, context) => {
 *     // context.client is now available
 *   });
 * ```
 */
export function withSystemClient<
  TParent = unknown,
  TArgs = unknown,
>(): Middleware<TParent, GraphQLContext, SystemContext, TArgs, TArgs> {
  return (parent, context, args) => {
    const client = getSystemClient(context);

    const enhancedContext: SystemContext = {
      ...context,
      client,
    } as SystemContext;

    return Promise.resolve({ context: enhancedContext, args });
  };
}

/**
 * Validation middleware — validates the input args against a Zod schema.
 *
 * Transforms the args type to match the inferred type from the Zod schema.
 * The validated input replaces `args.input`, providing full type safety.
 *
 * Throws a validation error if the input doesn't match the schema.
 *
 * @template TContext - The context type (passed through unchanged)
 * @template TSchema - The Zod schema type
 * @param schema - The Zod schema to validate against
 * @returns Middleware that validates and narrows the args type
 *
 * @example
 * ```typescript
 * createResolver<CreateDatasetPayload>()
 *   .use(withValidation(CreateDatasetSchema))
 *   .resolve(async (parent, args, context) => {
 *     // args.input is now typed as z.infer<typeof CreateDatasetSchema>
 *     // TypeScript knows args.input.name is a string, args.input.orgId is a string, etc.
 *     const name = args.input.name; // fully typed!
 *   });
 * ```
 */
export function withValidation<
  TContext extends GraphQLContext,
  TSchema extends z.ZodSchema,
>(
  schema: TSchema,
): Middleware<unknown, TContext, TContext, any, { input: z.infer<TSchema> }> {
  return async (parent, context, args) => {
    const validatedInput = validateInput<z.infer<TSchema>>(schema, args.input);

    return {
      context,
      args: { ...args, input: validatedInput },
    };
  };
}

/**
 * Logging middleware — logs resolver execution for debugging and monitoring.
 *
 * Logs the resolver name and args when the resolver starts executing.
 * Context and args are passed through unchanged.
 *
 * @template TContext - The context type (passed through unchanged)
 * @template TArgs - The args type (passed through unchanged)
 * @param label - A label for the resolver (typically the resolver name)
 * @returns Middleware that logs execution
 *
 * @example
 * ```typescript
 * createResolver<CreateDatasetPayload>()
 *   .use(withLogging('createDataset'))
 *   .use(withValidation(CreateDatasetSchema))
 *   .use(withOrgScopedClient(({ args }) => args.input.orgId))
 *   .resolve(async (parent, args, context) => {
 *     // Implementation
 *   });
 * ```
 */
export function withLogging<TContext, TArgs>(
  label: string,
): Middleware<unknown, TContext, TContext, TArgs, TArgs> {
  return async (parent, context, args) => {
    console.log(`[${label}] Starting`, { args });
    return { context, args };
  };
}
