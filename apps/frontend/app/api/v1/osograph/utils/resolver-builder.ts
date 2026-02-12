/**
 * Generic resolver builder for type-safe GraphQL resolver development.
 *
 * This module provides a fluent builder API for creating GraphQL resolvers with:
 * - Compile-time type safety through progressive type enhancement
 * - Composable middleware for auth, validation, logging, etc.
 * - Reduced boilerplate code (~30-50% less code per resolver)
 * - Full IntelliSense support
 *
 * Example usage:
 * ```typescript
 * export const createDataset = createResolver<CreateDatasetPayload>()
 *   .use(withValidation(CreateDatasetSchema))
 *   .use(requireOrgAccess((args) => args.input.orgId))
 *   .resolve(async (parent, args, context) => {
 *     // args.input is fully typed from schema
 *     // context.client, context.orgRole, context.userId are guaranteed to exist
 *     const { data } = await context.client.from('datasets').insert(...);
 *     return { dataset: data, success: true };
 *   });
 * ```
 */

import type { GraphQLResolveInfo } from "graphql";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import type {
  ResolverFn,
  ResolversTypes,
} from "@/app/api/v1/osograph/types/generated/types";

/**
 * Handler function for a resolver after all middleware have been applied.
 *
 * @template TResult - The return type of the resolver
 * @template TParent - The parent object type (for field resolvers)
 * @template TContext - The enhanced context type (with all middleware applied)
 * @template TArgs - The enhanced args type (after validation/transformation)
 */
type ResolverHandler<TResult, TParent, TContext, TArgs> = (
  parent: TParent,
  args: TArgs,
  context: TContext,
  info: GraphQLResolveInfo,
) => Promise<TResult> | TResult;

/**
 * A middleware function that transforms context and/or args.
 *
 * Middleware are applied sequentially in the order they're added via `.use()`.
 * Each middleware receives the output from the previous middleware and returns
 * potentially enhanced versions of context and args.
 *
 * @template TInputContext - The input context type
 * @template TOutputContext - The enhanced context type to return
 * @template TInputArgs - The input args type
 * @template TOutputArgs - The enhanced args type to return
 *
 * @returns A promise resolving to { context, args }
 *
 * Example:
 * ```typescript
 * const myMiddleware: Middleware<GraphQLContext, AuthenticatedContext, any, any> =
 *   async (context, args) => {
 *     const { client, userId } = getAuthenticatedClient(context);
 *     return {
 *       context: { ...context, client, userId } as AuthenticatedContext,
 *       args,
 *     };
 *   };
 * ```
 */
export type Middleware<TInputContext, TOutputContext, TInputArgs, TOutputArgs> =
  (
    context: TInputContext,
    args: TInputArgs,
  ) => Promise<{ context: TOutputContext; args: TOutputArgs }>;

/**
 * Builder class for creating type-safe GraphQL resolvers with composable middleware.
 *
 * Each call to `.use()` returns a NEW builder instance with updated type parameters,
 * ensuring full type safety. The middleware chain is captured via closures - no
 * array storage needed.
 *
 * @template TResult - The return type of the resolver
 * @template TParent - The parent object type (for field resolvers)
 * @template TContext - The current context type (enhanced by previous .use() calls)
 * @template TArgs - The current args type (enhanced by previous .use() calls)
 */
class ResolverBuilder<TResult, TParent, TContext, TArgs> {
  /**
   * Constructor stores a function that applies all middleware up to this point.
   *
   * @param applyMiddleware - Function that applies the middleware chain
   */
  constructor(
    private applyMiddleware: (
      context: any,
      args: any,
    ) => Promise<{ context: any; args: any }>,
  ) {}

  /**
   * Add a middleware to the resolver chain.
   *
   * Returns a NEW builder instance with updated type parameters. The previous
   * middleware logic is captured in a closure, so no array storage is needed.
   *
   * @template TNewContext - The enhanced context type after this middleware
   * @template TNewArgs - The enhanced args type after this middleware
   * @param middleware - The middleware function to add
   * @returns A new builder with enhanced types
   *
   * Example:
   * ```typescript
   * createResolver<MyPayload>()
   *   .use(requireAuth())
   *   .use(withValidation(MySchema))
   *   .resolve((parent, args, context) => {
   *     // context has AuthenticatedContext type
   *     // args has validated type from schema
   *   });
   * ```
   */
  use<TNewContext = TContext, TNewArgs = TArgs>(
    middleware: Middleware<TContext, TNewContext, TArgs, TNewArgs>,
  ): ResolverBuilder<TResult, TParent, TNewContext, TNewArgs> {
    const previousApply = this.applyMiddleware;

    // Return a new builder that captures the previous middleware chain
    return new ResolverBuilder<TResult, TParent, TNewContext, TNewArgs>(
      async (context, args) => {
        // Apply all previous middleware first
        const intermediate = await previousApply(context, args);
        // Then apply this middleware
        return await middleware(intermediate.context, intermediate.args);
      },
    );
  }

  /**
   * Build the final resolver function.
   *
   * This applies all middleware sequentially (via the captured closure chain)
   * and then calls the handler with the fully enhanced context and args.
   *
   * @param handler - The resolver implementation
   * @returns A GraphQL resolver function compatible with the generated types
   *
   * Example:
   * ```typescript
   * .resolve(async (parent, args, context, info) => {
   *   // All middleware have been applied
   *   // Full type safety for context and args
   *   return { success: true };
   * });
   * ```
   */
  resolve(
    handler: ResolverHandler<TResult, TParent, TContext, TArgs>,
  ): ResolverFn<TResult, TParent, GraphQLContext, TArgs> {
    const applyMiddleware = this.applyMiddleware;

    return async (parent, originalArgs, originalContext, info) => {
      // Apply all middleware via the captured closure chain
      const { context, args } = await applyMiddleware(
        originalContext,
        originalArgs,
      );

      // Call the handler with fully enhanced context and args
      return handler(parent, args, context, info);
    };
  }
}

export type ResolverTypeKeys = keyof ResolversTypes;

/**
 * Create a new resolver builder.
 *
 * This is the entry point for creating resolvers with the builder pattern.
 *
 * @template TResult - The return type of the resolver (should match a GraphQL type)
 * @template TParent - The parent object type (defaults to any for root resolvers)
 * @template TArgs - The args type (defaults to any, will be narrowed by validation)
 * @returns A new ResolverBuilder instance
 *
 * Example:
 * ```typescript
 * export const myMutation = createResolver<MyMutationPayload>()
 *   .use(withValidation(MySchema))
 *   .use(requireOrgAccess((args) => args.input.orgId))
 *   .resolve(async (parent, args, context) => {
 *     // Implementation
 *   });
 * ```
 */
export function createResolver<
  TResult extends ResolverTypeKeys,
  TParent = any,
  TArgs = any,
>(): ResolverBuilder<ResolversTypes[TResult], TParent, GraphQLContext, TArgs> {
  // Start with an identity middleware (no-op)
  return new ResolverBuilder<
    ResolversTypes[TResult],
    TParent,
    GraphQLContext,
    TArgs
  >(async (context, args) => ({ context, args }));
}
