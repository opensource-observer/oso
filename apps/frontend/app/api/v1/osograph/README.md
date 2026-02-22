# Refactoring Guide: GraphQL Resolvers with Strongly Typed Responses

## Overview

This document describes the NEW STYLE pattern for GraphQL resolvers using the `createResolver()` and `createResolversCollection()` builders. These utilities provide type-safe, composable middleware for access-control and validation. We should also use this in the new organization of resolvers that is actively being developed.

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
- Explicit authentication and access-control
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

## Tier Selection

Each resolver directory maps to exactly one middleware factory. Do not mix tiers.

| Directory       | Middleware                                          | Context Type                 |
| --------------- | --------------------------------------------------- | ---------------------------- |
| `organization/` | `withOrgScopedClient(getOrgId)`                     | `OrgScopedContext`           |
| `user/`         | `withAuthenticatedClient()`                         | `AuthenticatedClientContext` |
| `resource/`     | `withOrgResourceClient(type, getResourceId, perm?)` | `ResourceScopedContext`      |
| `system/`       | `withSystemClient()`                                | `SystemContext`              |

Rules enforced by osolint:

- Never call `createAdminClient()` directly in resolver files — the client comes through context
- Each directory uses only its designated middleware
- `withValidation()` always goes **before** the access-control middleware

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
  .use(withAuthenticatedClient())
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
      .use(withValidation(CreateDataModelInputSchema()))
      .use(withOrgScopedClient(({ args }) => args.input.orgId))
      .resolve(async (_, { input }, context) => {
        // context.client is available — no createAdminClient() needed
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

### `withOrgScopedClient(getOrgId)`

Validates user is authenticated and is a member of the specified org.

**Context Transition:** `GraphQLContext` → `OrgScopedContext`

**Context properties added:**

- `context.client` — Supabase admin client
- `context.orgId` — the organization being accessed
- `context.orgRole` — `"owner" | "admin" | "member"`
- `context.userId` — authenticated user's ID
- `context.authenticatedUser` — full user object (for JWT signing, external service calls)

**Use in:** `organization/**` resolvers

**Example:**

```typescript
.use(withValidation(CreateNotebookInputSchema()))
.use(withOrgScopedClient(({ args }) => args.input.orgId))
.resolve(async (_, { input }, context) => {
  // context.client ready — no createAdminClient() needed
  const { data } = await context.client.from("notebooks").insert({ ... });
})
```

### `withAuthenticatedClient()`

Validates user is authenticated (not anonymous).

**Context Transition:** `GraphQLContext` → `AuthenticatedClientContext`

**Context properties added:**

- `context.client` — Supabase admin client
- `context.userId` — authenticated user's ID
- `context.orgIds` — org IDs scoped by token type (API token → `[tokenOrgId]`, PAT → all user orgs)
- `context.orgScope` — `OrgScope` describing the authentication scope
- `context.authenticatedUser` — full user object (for JWT signing, external service calls)

**Use in:** `user/**` resolvers

**Example:**

```typescript
.use(withAuthenticatedClient())
.resolve(async (_, args, context) => {
  // context.client, context.userId, context.orgIds available
})
```

### `withOrgResourceClient(resourceType, getResourceId, requiredPermission?)`

Validates user has permission on the specified resource.

**Context Transition:** `GraphQLContext` → `ResourceScopedContext`

**Context properties added:**

- `context.client` — Supabase admin client
- `context.permissionLevel` — user's effective permission (`Exclude<PermissionLevel, "none">`)
- `context.resourceId` — the resource being accessed
- `context.authenticatedUser` — full user object (for JWT signing, Trino queries, etc.)

**Use in:** `resource/**` resolvers

**Example:**

```typescript
.use(withValidation(UpdateDataModelInputSchema()))
.use(withOrgResourceClient("data_model", ({ args }) => args.input.dataModelId, "write"))
.resolve(async (_, { input }, context) => {
  // context.client, context.permissionLevel, context.resourceId available
})
```

### `withSystemClient()`

Validates system credentials are present (internal calls only).

**Context Transition:** `GraphQLContext` → `SystemContext`

**Context properties added:**

- `context.client` — Supabase admin client with full access

**Use in:** `system/**` resolvers only

**Example:**

```typescript
.use(withSystemClient())
.resolve((_, args, context) => {
  // context.client is the admin client
})
```

### `withValidation(schema)`

Validates and types the `args.input` parameter using a Zod schema.

**Args Enhancement:** `any` → `{ input: z.infer<Schema> }`

**Always place before access-control middleware** so `args.input` is typed when the access-control middleware extracts IDs.

**Example:**

```typescript
.use(withValidation(CreateDataModelInputSchema()))
// Now args.input is fully typed from the schema
```

### `withLogging(label)`

Logs resolver execution for debugging and monitoring. Context and args pass through unchanged.

**Example:**

```typescript
.use(withLogging('createDataset'))
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

### Pattern 1: Org-Creation Mutation (`organization/**`)

**Use for:** Mutations that create or manage org-level resources

```typescript
const mutations = createResolversCollection<NotebookMutationResolvers>()
  .defineWithBuilder("createNotebook", (builder) => {
    return builder
      .use(withValidation(CreateNotebookInputSchema()))
      .use(withOrgScopedClient(({ args }) => args.input.orgId))
      .resolve(async (_, { input }, context) => {
        // context.client available — org membership already validated
        const { data, error } = await context.client
          .from("notebooks")
          .insert({
            org_id: input.orgId,
            name: input.name,
          })
          .select()
          .single();

        if (error) {
          throw ServerErrors.database("Failed to create notebook");
        }

        return {
          success: true,
          message: "Notebook created successfully",
          notebook: data,
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
    .use(withValidation(schema))
    .use(withOrgResourceClient("data_model", ({ args }) => getExistingModelId(args.input), "write"));
}

// Usage:
.defineWithBuilder("updateDataModel", (builder) => {
  return existingDataModelMiddleware(
    builder,
    UpdateDataModelInputSchema(),
    (input) => input.dataModelId,
  ).resolve(async (_, { input }, context) => {
    // context.client, context.permissionLevel, context.resourceId guaranteed
  });
})
```

### Pattern 3: Field Resolver with Resource Access (`resource/**`)

**Use for:** Field resolvers that require resource-level permission checks

```typescript
const dataModelTypeResolvers = {
  DataModel: {
    // Simple field mappings - no builder needed
    id: (parent) => parent.id,
    name: (parent) => parent.name,
    orgId: (parent) => parent.org_id,

    // Field resolver with auth - use builder
    previewData: createResolver<DataModelResolvers, "previewData">()
      .use(withOrgResourceClient("data_model", (parent) => parent.id, "read"))
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

### Pattern 4: System Resolver (`system/**`)

**Use for:** Internal operations like scheduler tasks that bypass user auth

```typescript
.defineWithBuilder("runScheduledJob", (builder) => {
  return builder
    .use(withSystemClient())
    .resolve(async (_, args, context) => {
      const { error } = await context.client
        .from("scheduled_jobs")
        .update({ last_run_at: new Date().toISOString() })
        .eq("id", args.jobId);

      if (error) {
        throw ServerErrors.database("Failed to update job");
      }

      return { success: true };
    });
})
```

---

## Complete Example: organization mutation

```typescript
import {
  createResolver,
  createResolversCollection,
} from "@/app/api/v1/osograph/utils/resolver-builder";
import {
  withOrgScopedClient,
  withValidation,
} from "@/app/api/v1/osograph/utils/resolver-middleware";

const mutations = createResolversCollection<OrgMutationResolvers>()
  .defineWithBuilder("addUserByEmail", (builder) => {
    return builder
      .use(withValidation(AddUserByEmailInputSchema()))
      .use(withOrgScopedClient(({ args }) => args.input.orgId))
      .resolve(async (_, { input }, context) => {
        const { data: userProfile } = await context.client
          .from("user_profiles")
          .select("id")
          .ilike("email", input.email.toLowerCase().trim())
          .single();

        if (!userProfile) {
          throw UserErrors.notFound();
        }

        const { data: member, error } = await context.client
          .from("users_by_organization")
          .insert({
            org_id: context.orgId,
            user_id: userProfile.id,
            user_role: input.role.toLowerCase(),
          })
          .select()
          .single();

        if (error) {
          throw ServerErrors.database("Failed to add user");
        }

        return { member, message: "User added successfully", success: true };
      });
  })
  .resolvers();
```

---

## When to Use Each Pattern

### Use `createResolversCollection()`

- Defining multiple mutations in one file
- Building a complete set of query resolvers
- When you want strong type safety across all resolvers

### Use `createResolver()` directly

- Single field resolver with auth/validation needs
- Custom resolvers that don't fit into a collection
- When you need to export the resolver individually

### Use plain functions

- Simple field mappings (e.g., `orgId: (parent) => parent.org_id`)
- Field resolvers without auth/validation needs
- Queries using `queryWithPagination()` utility

### Use custom middleware factories

- Shared patterns across multiple resolvers
- Complex validation logic
- Resource fetching that's reused

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
.use(withValidation(schema))          // 1. Validate input (args.input gets typed)
.use(withOrgScopedClient(...))        // 2. Access-control (uses typed args.input)
.resolve(...)                          // 3. Business logic
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
- [ ] Import the correct tier middleware from `utils/resolver-middleware`
- [ ] Import schemas from `types/generated/validation.ts`
- [ ] Convert mutations to use `createResolversCollection().defineWithBuilder()`
- [ ] Replace `requireAuth()` + `ensureOrgMembership()` with `withOrgScopedClient()` (org resolvers)
- [ ] Replace `requireAuth()` alone with `withAuthenticatedClient()` (user resolvers)
- [ ] Replace `getOrgResourceClient()` calls with `withOrgResourceClient()` (resource resolvers)
- [ ] Replace `getSystemClient()` calls with `withSystemClient()` (system resolvers)
- [ ] Place `withValidation()` **before** the access-control middleware
- [ ] Remove all `createAdminClient()` calls from resolver files — client comes from context
- [ ] Update field resolvers that need auth to use `createResolver()`
- [ ] Keep simple field resolvers as plain functions
- [ ] Keep queries using `queryWithPagination()` as-is
- [ ] Run `pnpm --filter frontend tsc --noEmit` — no TS errors
- [ ] Run `pnpm --filter frontend lint` — no `no-direct-admin-client` violations
- [ ] Remove unused imports

---

## Troubleshooting

### Type Error: "Type 'X' is not assignable to type 'Y'"

- Ensure you're using the correct resolver collection type
- Check that the resolver key matches the collection
- Verify middleware return types match expected context/args

### Context Property Not Found

- Add the appropriate tier middleware (see Tier Selection table above)
- `withValidation()` does not add context properties — it only narrows args
- Check middleware order — later middleware depend on earlier ones

### Args Not Typed Correctly

- Add `withValidation()` middleware **before** access-control middleware
- Ensure schema is imported from `types/generated/validation.ts`
- `withValidation()` narrows `args.input`, not `args` directly

### Builder Returns Wrong Type

- Check generic parameters on `createResolver()`
- Verify the resolver key exists in the collection type
- Ensure the builderFn returns the built resolver (call `.resolve()`)

### `authenticatedUser` Not Available

- `authenticatedUser` is available on all non-system context types
- `SystemContext` does not have `authenticatedUser` (use for internal-only ops)
- All three of `OrgScopedContext`, `AuthenticatedClientContext`, and `ResourceScopedContext` include `authenticatedUser`

---

## Additional Resources

- [resolver-builder.ts](apps/frontend/app/api/v1/osograph/utils/resolver-builder.ts) - Implementation
- [resolver-middleware.ts](apps/frontend/app/api/v1/osograph/utils/resolver-middleware.ts) - Middleware utilities
- [enhanced-context.ts](apps/frontend/app/api/v1/osograph/types/enhanced-context.ts) - Context type definitions
- [access-control.ts](apps/frontend/app/api/v1/osograph/utils/access-control.ts) - Access-control functions
- [data-model.ts](apps/frontend/app/api/v1/osograph/schema/resolvers/data-model.ts) - Legacy example (pre-migration)
