/**
 * Pre-built middleware library for common resolver patterns.
 *
 * This module provides factory functions that create middleware for:
 * - Authentication and authorization
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
 *   .use(requireOrgAccess((args) => args.input.orgId))
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
  AuthenticatedContext,
  OrgAccessContext,
} from "@/app/api/v1/osograph/types/enhanced-context";
import type { Middleware } from "@/app/api/v1/osograph/utils/resolver-builder";
import { requireAuthentication, requireOrgMembership as legacyRequireOrgMembership } from "./auth";

/**
 * Authentication enhancer - validates that the user is authenticated.
 *
 * Enhances the context with:
 * - `client`: Supabase admin client
 * - `userId`: The authenticated user's ID
 *
 * Throws an authentication error if the user is not logged in.
 *
 * @template TArgs - The args type (passed through unchanged)
 * @returns An enhancer that adds authentication to the context
 *
 * @example
 * ```typescript
 * createResolver<ViewerPayload>()
 *   .use(requireAuth())
 *   .resolve(async (parent, args, context) => {
 *     // context.client and context.userId are now available
 *     return { userId: context.userId };
 *   });
 * ```
 */
export function requireAuth<TArgs>(): Middleware<
  GraphQLContext,
  AuthenticatedContext,
  TArgs,
  TArgs
> {
  return async (context, args) => {
    const authenticatedUser = requireAuthentication(context.user);

    const enhancedContext: AuthenticatedContext = {
      ...context,
      authenticatedUser,
    } as AuthenticatedContext;

    return { context: enhancedContext, args };
  };
}

/**
 * Organization access enhancer - validates that the user is a member of the specified organization.
 *
 * Enhances the context with:
 * - `authenticatedUser`: The authenticated user's information
 * - `authenticatedUser`: The authenticated user's ID
 * - `orgRole`: The user's role in the organization (owner, admin, or member)
 * - `orgId`: The organization ID being accessed
 *
 * Throws an authorization error if the user is not a member of the organization.
 *
 * @template TArgs - The args type (must have a way to extract orgId)
 * @param getOrgId - Function to extract the organization ID from args
 * @returns An enhancer that adds organization access info to the context
 *
 * @example
 * ```typescript
 * createResolver<CreateDatasetPayload>()
 *   .use(withValidation(CreateDatasetSchema))
 *   .use(requireOrgMembership((args) => args.input.orgId))
 *   .resolve(async (parent, args, context) => {
 *     // context.client, context.orgRole, context.orgId are now available
 *     const isAdmin = context.orgRole === 'admin' || context.orgRole === 'owner';
 *   });
 * ```
 */
export function ensureOrgMembership<TArgs, TContext extends AuthenticatedContext>(
  getOrgId: (options: { context: TContext, args: TArgs }) => string,
): Middleware<TContext, OrgAccessContext<TContext>, TArgs, TArgs> {
  return async (context, args) => {
    const orgId = getOrgId({ context, args });

    await legacyRequireOrgMembership(
      context.authenticatedUser.userId,
      orgId,
    );

    const enhancedContext: OrgAccessContext<TContext> = {
      ...context,
      orgId,
    } as OrgAccessContext<TContext>;

    return { context: enhancedContext, args };
  };
}

/**
 * Validation enhancer - validates the input args against a Zod schema.
 *
 * Transforms the args type to match the inferred type from the Zod schema.
 * The validated input replaces `args.input`, providing full type safety.
 *
 * Throws a validation error if the input doesn't match the schema.
 *
 * @template TSchema - The Zod schema type
 * @param schema - The Zod schema to validate against
 * @returns An enhancer that validates and narrows the args type
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
export function withValidation<TContext extends GraphQLContext, TSchema extends z.ZodSchema>(
  schema: TSchema,
): Middleware<
  TContext,
  TContext,
  any,
  { input: z.infer<TSchema> }
> {
  return async (context, args) => {
    const validatedInput = validateInput(schema, args.input);

    return {
      context,
      args: { ...args, input: validatedInput },
    };
  };
}

/**
 * Logging enhancer - logs resolver execution for debugging and monitoring.
 *
 * Logs the resolver name and args when the resolver starts executing.
 * Context and args are passed through unchanged.
 *
 * @template TContext - The context type (passed through unchanged)
 * @template TArgs - The args type (passed through unchanged)
 * @param label - A label for the resolver (typically the resolver name)
 * @returns An enhancer that logs execution
 *
 * @example
 * ```typescript
 * createResolver<CreateDatasetPayload>()
 *   .use(withLogging('createDataset'))
 *   .use(withValidation(CreateDatasetSchema))
 *   .use(requireOrgAccess((args) => args.input.orgId))
 *   .resolve(async (parent, args, context) => {
 *     // Implementation
 *   });
 * ```
 */
export function withLogging<TContext, TArgs>(
  label: string,
): Middleware<TContext, TContext, TArgs, TArgs> {
  return async (context, args) => {
    console.log(`[${label}] Starting`, { args });
    return { context, args };
  };
}
