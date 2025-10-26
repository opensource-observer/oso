import type { GraphQLScalarType } from "graphql";
import type { GraphQLResolverMap } from "@apollo/subgraph/dist/schema-helper/resolverMap";

/**
 * Helper type to determine if a resolver map value is a resolver object
 * (i.e., not a scalar or enum).
 */
type IsResolverObject<T> = T extends GraphQLScalarType
  ? never
  : T extends { [key: string]: string | number }
    ? T extends { [key: string]: (...args: never[]) => unknown }
      ? T
      : never
    : T;

/**
 * Type for partial GraphQL resolver modules.
 * This is the same as `GraphQLResolverMap` but excludes `scalars` and `enums`,
 * so it only allows resolver objects (`Query`, `Mutation`, and type resolvers).
 */
export type GraphQLResolverModule<TContext = unknown> = {
  [typeName: string]: IsResolverObject<GraphQLResolverMap<TContext>[string]>;
};
