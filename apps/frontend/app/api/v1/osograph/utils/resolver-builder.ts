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
  MutationResolvers,
  QueryResolvers,
  Resolver,
  ResolverFn,
  ResolversTypes,
} from "@/app/api/v1/osograph/types/generated/types";

type EmptyObject = object;

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
export class ResolverBuilder<TResult, TParent, TContext, TArgs> {
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

type IsExactlyUnknown<T> = [T] extends [unknown]
  ? [unknown] extends [T]
    ? true
    : false
  : false;

export type ResolverTypeKeys = keyof ResolversTypes;
export type QueryResolverTypeKeys = keyof QueryResolvers;
export type MutationResolverTypeKeys = keyof MutationResolvers;

type InferParentIfResolver<T> =
  T extends Resolver<any, infer P, any, any> ? P : unknown;
type InferArgsIfResolver<T> =
  T extends Resolver<any, any, any, infer A> ? A : unknown;
type InferContextIfResolver<T> =
  T extends Resolver<any, any, infer C, any> ? C : unknown;
type InferResultIfResolver<T> =
  T extends Resolver<infer R, any, any, any> ? R : unknown;

type ResolveParent<TFn, TParent> =
  IsExactlyUnknown<TParent> extends true ? InferParentIfResolver<TFn> : TParent;

type ResolveArgs<TFn, TArgs> =
  IsExactlyUnknown<TArgs> extends true ? InferArgsIfResolver<TFn> : TArgs;

type ResolveContext<TFn, TContext> =
  IsExactlyUnknown<TContext> extends true
    ? InferContextIfResolver<TFn>
    : TContext;

export type AssertIsResolver<T> =
  T extends Resolver<any, any, any, any> ? T : never;

/**
 * Allows creating a resolver builder with a fluent API for adding middleware
 * and building a resolver function. This ensures type safety and hopefully
 * reduces boilerplate when creating GraphQL resolvers.
 *
 * Type parameters are inferred from the final resolver handler, so should only
 * need to specify the TResolvers and TResolverKey when creating a builder.
 *
 * @template TResolversCollection - The type containing all resolvers (e.g. QueryResolvers)
 * @template TResolverKey - The specific resolver key to build (e.g. "dataModels")
 * @template TResolver - The resolver type inferred from TResolvers[TResolverKey]
 * @template TResult - The return type of the resolver (inferred from TResolver)
 * @template TParent - The parent object type (for field resolvers, inferred from TResolver)
 * @template TContext - The context type for the resolver (inferred from TResolver)
 * @template TArgs - The arguments type for the resolver (inferred from TResolver)
 *
 * @returns A ResolverBuilder instance with the specified type parameters
 */
export function createResolver<
  TResolversCollection,
  TResolverKey extends string & keyof TResolversCollection,
  TResolver extends Resolver<
    TResult,
    TParent,
    TContext,
    TArgs
  > = AssertIsResolver<TResolversCollection[TResolverKey]>,
  TResult = InferResultIfResolver<TResolver>,
  TParent = InferParentIfResolver<TResolver>,
  TContext = InferContextIfResolver<TResolver>,
  TArgs = InferArgsIfResolver<TResolver>,
>(): ResolverBuilder<
  TResult,
  ResolveParent<TResolver, TParent>,
  ResolveContext<TResolver, TContext>,
  ResolveArgs<TResolver, TArgs>
> {
  // Start with an identity middleware (no-op)
  return new ResolverBuilder(async (context, args) => ({ context, args }));
}

interface CollectionBuilder<
  TResolversCollection,
  TCompletedResolvers = EmptyObject,
> {
  define<
    TKey extends string & keyof TResolversCollection,
    TNewCompletedResolvers = TCompletedResolvers & {
      [K in TKey]: TResolversCollection[TKey];
    },
  >(
    key: TKey,
    resolver: TResolversCollection[TKey],
  ): CollectionBuilder<TResolversCollection, TNewCompletedResolvers>;
  defineWithBuilder<
    TKey extends string & keyof TResolversCollection,
    TNewCompletedResolvers = TCompletedResolvers & {
      [K in TKey]: TResolversCollection[TKey];
    },
    TResolver extends Resolver<any, any, any, any> = AssertIsResolver<
      TResolversCollection[TKey]
    >,
    TResult = InferResultIfResolver<TResolver>,
    TParent = InferParentIfResolver<TResolver>,
    TContext = InferContextIfResolver<TResolver>,
    TArgs = InferArgsIfResolver<TResolver>,
  >(
    key: TKey,
    builderFn: (
      builder: ResolverBuilder<
        TResult,
        ResolveParent<TResolver, TParent>,
        ResolveContext<TResolver, TContext>,
        ResolveArgs<TResolver, TArgs>
      >,
    ) => Resolver<TResult, TParent, TContext, TArgs>,
  ): CollectionBuilder<TResolversCollection, TNewCompletedResolvers>;
  resolvers(): TCompletedResolvers;
}

/**
 * Define a group of resolvers (e.g. all Query resolvers) with a fluent API.
 *
 * This allows you to build up a collection of resolvers with type safety and less boilerplate.
 * Each call to .define() or .defineWithBuilder() adds a resolver to the collection.
 * The .resolvers() method returns the completed collection, which can be spread into the final resolvers export.
 *
 * @template TResolversCollection - The type containing all resolvers (e.g. QueryResolvers)
 * @template TCompletedResolvers - The type of resolvers that have been defined so far (used for type safety)
 * @param accumulated - The accumulated resolvers so far (usually not passed in directly, used for recursion)
 *
 * @returns A collection builder for defining resolvers
 */
export function createResolversCollection<
  TResolversCollection,
  TCompletedResolvers = EmptyObject,
>(
  accumulated?: TCompletedResolvers,
): CollectionBuilder<TResolversCollection, TCompletedResolvers> {
  const add = <
    TKey extends string & keyof TResolversCollection,
    TNewCompletedResolvers = TCompletedResolvers & {
      [K in TKey]: TResolversCollection[TKey];
    },
  >(
    key: TKey,
    resolver: TResolversCollection[TKey],
  ): CollectionBuilder<TResolversCollection, TNewCompletedResolvers> => {
    const newAccumulated = {
      ...accumulated,
      [key]: resolver,
    } as TNewCompletedResolvers;
    return createResolversCollection<
      TResolversCollection,
      TNewCompletedResolvers
    >(newAccumulated);
  };
  return {
    define<
      TKey extends string & keyof TResolversCollection,
      TCompletedResolvers = EmptyObject,
      TNewCompletedResolvers = TCompletedResolvers & {
        [K in TKey]: TResolversCollection[K];
      },
    >(key: TKey, resolver: TResolversCollection[TKey]) {
      return add<TKey, TNewCompletedResolvers>(key, resolver);
    },
    defineWithBuilder<
      TKey extends string & keyof TResolversCollection,
      TNewCompletedResolvers = TCompletedResolvers & {
        [K in TKey]: TResolversCollection[K];
      },
      TResolver extends Resolver<any, any, any, any> = AssertIsResolver<
        TResolversCollection[TKey]
      >,
      TResult = InferResultIfResolver<TResolver>,
      TParent = InferParentIfResolver<TResolver>,
      TContext = InferContextIfResolver<TResolver>,
      TArgs = InferArgsIfResolver<TResolver>,
    >(
      key: TKey,
      builderFn: (
        builder: ResolverBuilder<
          TResult,
          ResolveParent<TResolver, TParent>,
          ResolveContext<TResolver, TContext>,
          ResolveArgs<TResolver, TArgs>
        >,
      ) => Resolver<TResult, TParent, TContext, TArgs>,
    ) {
      const builder = createResolver<
        TResolversCollection,
        TKey,
        TResolver,
        TResult,
        TParent,
        TContext,
        TArgs
      >();
      const builtResolver = builderFn(builder) as TResolversCollection[TKey];
      return add<TKey, TNewCompletedResolvers>(key, builtResolver);
    },
    resolvers() {
      // This is a bit of a hack - we need to return the accumulated resolvers,
      // but since we're not storing them in an array, we can't actually accumulate them.
      // In practice, this means you can only call .add() once per collection, which is a limitation.
      // To fully implement this with multiple .add() calls, we'd need to change the design to store resolvers in an array or similar structure.
      if (!accumulated) {
        throw new Error("No resolvers defined");
      }
      return accumulated;
    },
  };
}
