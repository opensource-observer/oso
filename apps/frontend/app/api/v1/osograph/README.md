# Refactoring Guide: GraphQL Resolvers with Strongly Typed Responses

## Overview

This document describes the NEW STYLE pattern for GraphQL resolvers using the `createResolver()` and `createResolversCollection()` builders. These utilities provide type-safe, composable middleware for authentication, validation, and org membership checks. We should also use this in the new organization of resolvers that is actively being developed.

## Core Concepts

### 1. Resolver Builder Pattern

The `createResolver()` function creates a fluent builder for individual
resolvers with progressive type enhancement through middleware composition. This
isn't always needed for simple field resolvers, but is ideal for mutations and
queries that require authentication and validation.

**Key Benefits:**

- Full type safety with TypeScript inference
- Composable middleware chain
- Reduced boilerplate (30-50% less code)
- Explicit authentication and validation
- IntelliSense support throughout

### 2. Resolvers Collection Pattern

The `createResolversCollection()` function creates a fluent builder for defining multiple related resolvers (e.g., all mutations) with type safety.

**Key Benefits:**

- Type-safe resolver collection building
- Enforces that all resolver keys match the expected type
- Fluent API for defining resolvers one by one
- Returns properly typed resolver object
- Using this builder is optional but removes the need to specify types on each
  individual resolver

---

## API Reference

### `createResolver<TResolversCollection, TResolverKey>()`

Creates a builder for a single resolver with type inference from the GraphQL schema.

**Type Parameters:**

- `TResolversCollection` - The resolver collection type (e.g., `DataModelResolvers`, `MutationResolvers`)
- `TResolverKey` - The specific resolver key (e.g., `"previewData"`, `"createDataModel"`)

**Returns:** `ResolverBuilder` instance

**Example:**

```typescript
const previewData = createResolver<DataModelResolvers, "previewData">()
  .use(requireAuth())
  .resolve(async (parent, args, context) => {
    // parent, args, and context are fully typed
    return executePreviewQuery(/* ... */);
  });
```

### `createResolversCollection<TResolversCollection>()`

Creates a builder for defining multiple resolvers in a type-safe collection.

**Type Parameters:**

- `TResolversCollection` - The resolver collection type (e.g., `MutationResolvers`)

**Returns:** `CollectionBuilder` instance with methods:

#### `.defineWithBuilder(key, builderFn)`

Defines a resolver using the builder pattern with middleware.

**Parameters:**

- `key` - The resolver key (must be a key of `TResolversCollection`)
- `builderFn` - Function that receives a `ResolverBuilder` and returns the built resolver

**Example:**

```typescript
createResolversCollection<DataModelMutationResolvers>().defineWithBuilder(
  "createDataModel",
  (builder) => {
    return builder
      .use(requireAuth())
      .use(withValidation(CreateDataModelInputSchema()))
      .use(ensureOrgMembership(({ args }) => args.input.orgId))
      .resolve(async (_, { input }, context) => {
        // Implementation
      });
  },
);
```

#### `.define(key, resolver)`

Defines a resolver directly without using the builder (for pre-built resolvers).

**Parameters:**

- `key` - The resolver key
- `resolver` - The resolver function

**Example:**

```typescript
.define("someResolver", async (parent, args, context) => {
  // Direct resolver implementation
})
```

#### `.resolvers()`

Returns the completed resolver collection.

**Returns:** Object with all defined resolvers

**Example:**

```typescript
const mutations = createResolversCollection<MutationResolvers>()
  .defineWithBuilder("create", (builder) => /* ... */)
  .defineWithBuilder("update", (builder) => /* ... */)
  .resolvers(); // Returns { create: ..., update: ... }
```

---

## Middleware Reference

### `requireAuth()`

Validates user authentication and adds `authenticatedUser` to context.

**Context Enhancement:** `GraphQLContext` → `AuthenticatedContext`

**Example:**

```typescript
.use(requireAuth())
// Now context.authenticatedUser is guaranteed to exist
```

### `withValidation(schema)`

Validates and types the `args.input` parameter using a Zod schema.

**Args Enhancement:** `any` → `{ input: z.infer<Schema> }`

**Example:**

```typescript
.use(withValidation(CreateDataModelInputSchema()))
// Now args.input is fully typed from the schema
```

### `ensureOrgMembership(getOrgId)`

Validates user is a member of the specified organization.

**Context Enhancement:** Adds `orgId` to context (requires `AuthenticatedContext`)

**Example:**

```typescript
.use(ensureOrgMembership(({ args }) => args.input.orgId))
// Now context.orgId is guaranteed to exist
```

### Custom Middleware

You can create custom middleware inline:

```typescript
.use(async (context, args) => {
  // Custom logic
  const data = await fetchSomething(args.input.id);

  return {
    context: { ...context, data },
    args,
  };
})
```

---

## Implementation Patterns

### Pattern 1: Simple Mutation

**Use for:** Basic mutations with auth and validation

```typescript
const mutations = createResolversCollection<DataModelMutationResolvers>()
  .defineWithBuilder("createDataModel", (builder) => {
    return builder
      .use(requireAuth())
      .use(withValidation(CreateDataModelInputSchema()))
      .use(ensureOrgMembership(({ args }) => args.input.orgId))
      .resolve(async (_, { input }, context) => {
        const supabase = createAdminClient();
        const { data, error } = await supabase
          .from("model")
          .insert({
            org_id: input.orgId,
            dataset_id: input.datasetId,
            name: input.name,
            is_enabled: input.isEnabled ?? true,
          })
          .select()
          .single();

        if (error) {
          throw ServerErrors.database("Failed to create dataModel");
        }

        return {
          success: true,
          message: "DataModel created successfully",
          dataModel: data,
        };
      });
  })
  .resolvers();
```

### Pattern 2: Reusable Middleware Factory

**Use for:** Common patterns across multiple mutations (e.g., operating on existing resources)

```typescript
function existingDataModelMiddleware<TSchema extends z.ZodSchema>(
  builder: ResolverBuilder<any, any, any, any>,
  schema: TSchema,
  getExistingModelId: (input: z.infer<TSchema>) => string,
) {
  return builder
    .use(requireAuth())
    .use(withValidation(schema))
    .use(async (context, args) => {
      // Fetch and validate existing resource
      const existingModelId = getExistingModelId(args.input);
      const supabase = createAdminClient();
      const { data: dataModel, error } = await supabase
        .from("model")
        .select("org_id")
        .eq("id", existingModelId)
        .single();

      if (error || !dataModel) {
        throw ResourceErrors.notFound("DataModel", existingModelId);
      }

      return {
        context: {
          ...context,
          dataModel,
          supabase,
        },
        args,
      };
    })
    .use(ensureOrgMembership(({ context }) => context.dataModel.org_id));
}

// Usage:
.defineWithBuilder("updateDataModel", (builder) => {
  return existingDataModelMiddleware(
    builder,
    UpdateDataModelInputSchema(),
    (input) => input.dataModelId,
  ).resolve(async (_, { input }, context) => {
    // context.dataModel and context.supabase are guaranteed
    // Org membership is already validated
  });
})
```

### Pattern 3: Field Resolver with Auth

**Use for:** Field resolvers that require authentication

```typescript
const dataModelTypeResolvers = {
  DataModel: {
    // Simple field mappings - no builder needed
    id: (parent) => parent.id,
    name: (parent) => parent.name,
    orgId: (parent) => parent.org_id,

    // Field resolver with auth - use builder
    previewData: createResolver<DataModelResolvers, "previewData">()
      .use(requireAuth())
      .resolve(async (parent, _args, context) => {
        const tableId = generateTableId("USER_MODEL", parent.id);

        return executePreviewQuery(
          parent.org_id,
          parent.dataset_id,
          tableId,
          context.authenticatedUser,
          parent.name,
        );
      }),
  },
};
```

### Pattern 4: Custom Middleware for Special Cases

**Use for:** Mutations that don't follow standard patterns

```typescript
.defineWithBuilder("deleteDataModel", (builder) => {
  return builder
    .use(requireAuth())
    .use(async (context, args) => {
      // Custom validation logic
      const supabase = createAdminClient();
      const { data: dataModel, error } = await supabase
        .from("model")
        .select("org_id")
        .eq("id", args.id)
        .single();

      if (error || !dataModel) {
        throw ResourceErrors.notFound("DataModel", args.id);
      }

      await requireOrgMembership(
        context.authenticatedUser.userId,
        dataModel.org_id,
      );

      return {
        context: { ...context, dataModel, supabase },
        args,
      };
    })
    .resolve(async (_, { id }, context) => {
      const { supabase } = context;
      const { error } = await supabase
        .from("model")
        .update({ deleted_at: new Date().toISOString() })
        .eq("id", id);

      if (error) {
        throw ServerErrors.database("Failed to delete data model");
      }

      return {
        success: true,
        message: "DataModel deleted successfully",
      };
    });
})
```

---

## Complete Example: data-model.ts

Here's the complete implementation showing all patterns:

```typescript
import {
  createResolver,
  createResolversCollection,
} from "@/app/api/v1/osograph/utils/resolver-builder";
import {
  requireAuth,
  ensureOrgMembership,
  withValidation,
} from "@/app/api/v1/osograph/utils/resolver-middleware";

// Type definitions
type DataModelQueryResolvers = Pick<QueryResolvers, "dataModels">;
type DataModelMutationResolvers = Pick<
  Required<MutationResolvers>,
  | "createDataModel"
  | "updateDataModel"
  | "createDataModelRevision"
  | "createDataModelRelease"
  | "deleteDataModel"
>;

type DataModelRelatedResolvers = {
  Query: DataModelQueryResolvers;
  Mutation: DataModelMutationResolvers;
  DataModel: DataModelResolvers;
  DataModelRevision: DataModelRevisionResolvers;
  DataModelRelease: DataModelReleaseResolvers;
};

// Reusable middleware factory
function existingDataModelMiddleware<TSchema extends z.ZodSchema>(
  builder: ResolverBuilder<any, any, any, any>,
  schema: TSchema,
  getExistingModelId: (input: z.infer<TSchema>) => string,
) {
  return builder
    .use(requireAuth())
    .use(withValidation(schema))
    .use(async (context, args) => {
      const existingModelId = getExistingModelId(args.input);
      const supabase = createAdminClient();
      const { data: dataModel, error } = await supabase
        .from("model")
        .select("org_id")
        .eq("id", existingModelId)
        .single();

      if (error || !dataModel) {
        throw ResourceErrors.notFound("DataModel", existingModelId);
      }

      return {
        context: { ...context, dataModel, supabase },
        args,
      };
    })
    .use(ensureOrgMembership(({ context }) => context.dataModel.org_id));
}

// Mutations using createResolversCollection
const mutations = createResolversCollection<DataModelMutationResolvers>()
  .defineWithBuilder("createDataModel", (builder) => {
    return builder
      .use(requireAuth())
      .use(withValidation(CreateDataModelInputSchema()))
      .use(ensureOrgMembership(({ args }) => args.input.orgId))
      .resolve(async (_, { input }) => {
        const supabase = createAdminClient();
        const { data, error } = await supabase
          .from("model")
          .insert({
            org_id: input.orgId,
            dataset_id: input.datasetId,
            name: input.name,
            is_enabled: input.isEnabled ?? true,
          })
          .select()
          .single();

        if (error) {
          throw ServerErrors.database("Failed to create dataModel");
        }

        return {
          success: true,
          message: "DataModel created successfully",
          dataModel: data,
        };
      });
  })
  .defineWithBuilder("updateDataModel", (builder) => {
    return existingDataModelMiddleware(
      builder,
      UpdateDataModelInputSchema(),
      (input) => input.dataModelId,
    ).resolve(async (_, { input }, context) => {
      const { supabase } = context;
      const updateData: ModelUpdate = {};
      if (input.name) updateData.name = input.name;
      if (input.isEnabled !== undefined)
        updateData.is_enabled = input.isEnabled;
      if (Object.keys(updateData).length > 0) {
        updateData.updated_at = new Date().toISOString();
      }

      const { data, error } = await supabase
        .from("model")
        .update(updateData)
        .eq("id", input.dataModelId)
        .select()
        .single();

      if (error) {
        throw ServerErrors.database("Failed to update dataModel");
      }

      return {
        success: true,
        message: "DataModel updated successfully",
        dataModel: data,
      };
    });
  })
  .defineWithBuilder("deleteDataModel", (builder) => {
    return builder
      .use(requireAuth())
      .use(async (context, args) => {
        const supabase = createAdminClient();
        const { data: dataModel, error } = await supabase
          .from("model")
          .select("org_id")
          .eq("id", args.id)
          .single();

        if (error || !dataModel) {
          throw ResourceErrors.notFound("DataModel", args.id);
        }

        await requireOrgMembership(
          context.authenticatedUser.userId,
          dataModel.org_id,
        );

        return {
          context: { ...context, dataModel, supabase },
          args,
        };
      })
      .resolve(async (_, { id }, context) => {
        const { supabase } = context;
        const { error } = await supabase
          .from("model")
          .update({ deleted_at: new Date().toISOString() })
          .eq("id", id);

        if (error) {
          throw ServerErrors.database("Failed to delete data model");
        }

        return {
          success: true,
          message: "DataModel deleted successfully",
        };
      });
  })
  .resolvers();

// Queries using queryWithPagination utility
const queries: DataModelQueryResolvers = {
  dataModels: async (_, args, context) => {
    return queryWithPagination(args, context, {
      tableName: "model",
      whereSchema: DataModelWhereSchema,
      requireAuth: true,
      filterByUserOrgs: true,
      basePredicate: {
        is: [{ key: "deleted_at", value: null }],
      },
    });
  },
};

// Field resolvers
const dataModelTypeResolvers = {
  DataModel: {
    id: (parent) => parent.id,
    name: (parent) => parent.name,
    orgId: (parent) => parent.org_id,
    organization: (parent) => getOrganization(parent.org_id),
    createdAt: (parent) => new Date(parent.created_at),
    updatedAt: (parent) => new Date(parent.updated_at),

    // Field resolver with auth
    previewData: createResolver<DataModelResolvers, "previewData">()
      .use(requireAuth())
      .resolve(async (parent, _args, context) => {
        const tableId = generateTableId("USER_MODEL", parent.id);
        return executePreviewQuery(
          parent.org_id,
          parent.dataset_id,
          tableId,
          context.authenticatedUser,
          parent.name,
        );
      }),
  },

  DataModelRevision: {
    id: (parent) => parent.id,
    name: (parent) => parent.name,
    orgId: (parent) => parent.org_id,
    createdAt: (parent) => new Date(parent.created_at),
    // ... other field resolvers
  },

  DataModelRelease: {
    id: (parent) => parent.id,
    orgId: (parent) => parent.org_id,
    createdAt: (parent) => new Date(parent.created_at),
    updatedAt: (parent) => new Date(parent.updated_at),
    // ... other field resolvers
  },
};

// Final export
export const dataModelResolvers: DataModelRelatedResolvers = {
  Query: queries,
  Mutation: mutations,
  ...dataModelTypeResolvers,
};
```

---

## When to Use Each Pattern

### Use `createResolversCollection()`

- ✅ Defining multiple mutations in one file
- ✅ Building a complete set of query resolvers
- ✅ When you want strong type safety across all resolvers

### Use `createResolver()` directly

- ✅ Single field resolver with auth/validation needs
- ✅ Custom resolvers that don't fit into a collection
- ✅ When you need to export the resolver individually

### Use plain functions

- ✅ Simple field mappings (e.g., `orgId: (parent) => parent.org_id`)
- ✅ Field resolvers without auth/validation needs
- ✅ Queries using `queryWithPagination()` utility

### Use custom middleware factories

- ✅ Shared patterns across multiple resolvers
- ✅ Complex validation logic
- ✅ Resource fetching that's reused

---

## Best Practices

### 1. Type Safety

Always specify the resolver collection and key types:

```typescript
createResolver<DataModelResolvers, "previewData">();
```

### 2. Middleware Order

Apply middleware in logical order:

```typescript
.use(requireAuth())           // 1. Authenticate
.use(withValidation(schema))  // 2. Validate input
.use(ensureOrgMembership(...)) // 3. Check permissions
.resolve(...)                  // 4. Business logic
```

### 3. Error Handling

Use semantic error types:

```typescript
throw ResourceErrors.notFound("DataModel", id);
throw ServerErrors.database("Failed to create resource");
```

### 4. Return Type Consistency

Match GraphQL schema return types:

```typescript
return {
  success: true,
  message: "Operation successful",
  dataModel: data, // Include the resource if schema expects it
};
```

### 5. Date Handling

Convert date strings to Date objects for DateTime scalars:

```typescript
createdAt: (parent) => new Date(parent.created_at);
```

### 6. Nullable Field Handling

Transform database nulls to match GraphQL schema:

```typescript
dependsOn: (parent) => parent.depends_on?.map(...) ?? null
```

---

## Migration Checklist

When refactoring resolvers to NEW STYLE:

- [ ] Import `createResolver` and/or `createResolversCollection`
- [ ] Import middleware: `requireAuth`, `withValidation`, `ensureOrgMembership`
- [ ] Import schemas from `types/generated/validation.ts`
- [ ] Convert mutations to use `createResolversCollection().defineWithBuilder()`
- [ ] Replace manual auth checks with `requireAuth()` middleware
- [ ] Replace manual validation with `withValidation()` middleware
- [ ] Replace manual org checks with `ensureOrgMembership()` middleware
- [ ] Update field resolvers that need auth to use `createResolver()`
- [ ] Keep simple field resolvers as plain functions
- [ ] Keep queries using `queryWithPagination()` as-is
- [ ] Verify all types are correct (no TypeScript errors)
- [ ] Test authentication, validation, and org membership checks
- [ ] Remove unused imports

---

## Troubleshooting

### Type Error: "Type 'X' is not assignable to type 'Y'"

- Ensure you're using the correct resolver collection type
- Check that the resolver key matches the collection
- Verify middleware return types match expected context/args

### Context Property Not Found

- Add the appropriate middleware (e.g., `requireAuth()` for `context.authenticatedUser`)
- Check middleware order - later middleware depend on earlier ones

### Args Not Typed Correctly

- Add `withValidation()` middleware with the correct schema
- Ensure schema is imported from `types/generated/validation.ts`

### Builder Returns Wrong Type

- Check generic parameters on `createResolver()`
- Verify the resolver key exists in the collection type
- Ensure the builderFn returns the built resolver (call `.resolve()`)

---

## Additional Resources

- [resolver-builder.ts](apps/frontend/app/api/v1/osograph/utils/resolver-builder.ts) - Implementation
- [resolver-middleware.ts](apps/frontend/app/api/v1/osograph/utils/resolver-middleware.ts) - Middleware utilities
- [data-model.ts](apps/frontend/app/api/v1/osograph/schema/resolvers/data-model.ts) - Complete example
