---
name: osograph-resolver-migration
description: Guides migration of osograph GraphQL resolvers from the legacy direct pattern to the typed builder pattern with access-control middleware. Use when migrating resolvers in apps/frontend/app/api/v1/osograph/schema/resolvers/{organization,user,resource,system}/. Covers tier selection, middleware chaining, context types, and osolint compliance.
license: MIT
metadata:
  author: Oso Team
  version: 1.0.0
  source: https://github.com/opensource-observer/oso
---

# osograph Resolver Migration Guide

## Overview

This skill guides migration of legacy osograph GraphQL resolvers to the typed builder pattern with typed access-control middleware.

**Why the builder pattern?**

- Resolvers never call `createAdminClient()` directly — the Supabase client comes through context from the middleware
- osolint enforces `no-direct-admin-client` in resolver files
- 4 context types give compile-time guarantees about what's available in each resolver tier
- `withValidation()` narrows `args.input` before access-control middleware reads IDs from it

---

## Tier → Middleware Mapping

| Directory       | Middleware                                          | Context Type                 |
| --------------- | --------------------------------------------------- | ---------------------------- |
| `organization/` | `withOrgScopedClient(getOrgId)`                     | `OrgScopedContext`           |
| `user/`         | `withAuthenticatedClient()`                         | `AuthenticatedClientContext` |
| `resource/`     | `withOrgResourceClient(type, getResourceId, perm?)` | `ResourceScopedContext`      |
| `system/`       | `withSystemClient()`                                | `SystemContext`              |

**Rule:** Each file in a resolver directory uses only its designated middleware. Never mix tiers.

---

## Context Type Properties

### `OrgScopedContext` (organization/)

```typescript
context.client; // SupabaseAdminClient
context.orgId; // string
context.orgRole; // "owner" | "admin" | "member"
context.userId; // string
context.authenticatedUser; // AuthenticatedUser (for JWT, Trino, etc.)
```

### `AuthenticatedClientContext` (user/)

```typescript
context.client; // SupabaseAdminClient
context.userId; // string
context.orgIds; // string[] (scoped by API token or all user orgs)
context.orgScope; // OrgScope
context.authenticatedUser; // AuthenticatedUser
```

### `ResourceScopedContext` (resource/)

```typescript
context.client; // SupabaseAdminClient
context.permissionLevel; // Exclude<PermissionLevel, "none">
context.resourceId; // string
context.authenticatedUser; // AuthenticatedUser (for JWT, Trino, etc.)
```

### `SystemContext` (system/)

```typescript
context.client; // SupabaseAdminClient (full admin access)
// No authenticatedUser — system calls bypass user auth
```

---

## Migration Checklist

### Per-file steps

1. **Determine tier** — Which subdirectory is this resolver in?
2. **Pick the middleware** — Use the Tier → Middleware table above
3. **Import from correct modules:**
   ```typescript
   import {
     createResolver,
     createResolversCollection,
   } from "@/app/api/v1/osograph/utils/resolver-builder";
   import {
     withOrgScopedClient, // or whichever tier applies
     withValidation,
     withLogging, // optional
   } from "@/app/api/v1/osograph/utils/resolver-middleware";
   import { MyInputSchema } from "@/app/api/v1/osograph/types/generated/validation";
   ```
4. **Wrap mutations** with `createResolversCollection().defineWithBuilder()`
5. **Wrap authenticated field resolvers** with `createResolver()`
6. **Remove `createAdminClient()`** — use `context.client` instead
7. **Order middleware correctly:**
   ```typescript
   .use(withValidation(MySchema()))           // 1. Validate (types args.input)
   .use(withOrgScopedClient(({ args }) => args.input.orgId))  // 2. Access-control
   .resolve(...)                               // 3. Business logic
   ```
8. **Run verification:**
   - `pnpm --filter frontend exec tsc --noEmit`
   - `pnpm --filter frontend lint`

---

## Code Templates

### Template: organization/ mutation

```typescript
import { createResolversCollection } from "@/app/api/v1/osograph/utils/resolver-builder";
import {
  withOrgScopedClient,
  withValidation,
} from "@/app/api/v1/osograph/utils/resolver-middleware";
import { MyCreateInputSchema } from "@/app/api/v1/osograph/types/generated/validation";
import { ServerErrors } from "@/app/api/v1/osograph/utils/errors";

export const xxxMutations = createResolversCollection<XxxMutationResolvers>()
  .defineWithBuilder("createXxx", (builder) => {
    return builder
      .use(withValidation(MyCreateInputSchema()))
      .use(withOrgScopedClient(({ args }) => args.input.orgId))
      .resolve(async (_, { input }, context) => {
        const { data, error } = await context.client
          .from("xxx_table")
          .insert({ org_id: context.orgId, name: input.name })
          .select()
          .single();

        if (error) throw ServerErrors.database("Failed to create Xxx");

        return { success: true, message: "Xxx created", xxx: data };
      });
  })
  .resolvers();
```

### Template: user/ resolver

```typescript
import { createResolver } from "@/app/api/v1/osograph/utils/resolver-builder";
import { withAuthenticatedClient } from "@/app/api/v1/osograph/utils/resolver-middleware";

export const viewerResolver = createResolver<QueryResolvers, "viewer">()
  .use(withAuthenticatedClient())
  .resolve(async (_, _args, context) => {
    // context.client, context.userId, context.orgIds available
    const { data } = await context.client
      .from("user_profiles")
      .select("*")
      .eq("id", context.userId)
      .single();

    return data;
  });
```

### Template: resource/ mutation

```typescript
import { createResolversCollection } from "@/app/api/v1/osograph/utils/resolver-builder";
import {
  withOrgResourceClient,
  withValidation,
} from "@/app/api/v1/osograph/utils/resolver-middleware";
import { UpdateXxxInputSchema } from "@/app/api/v1/osograph/types/generated/validation";
import { ServerErrors } from "@/app/api/v1/osograph/utils/errors";

export const xxxMutations = createResolversCollection<XxxMutationResolvers>()
  .defineWithBuilder("updateXxx", (builder) => {
    return builder
      .use(withValidation(UpdateXxxInputSchema()))
      .use(
        withOrgResourceClient(
          "data_model",
          ({ args }) => args.input.xxxId,
          "write",
        ),
      )
      .resolve(async (_, { input }, context) => {
        // context.client, context.permissionLevel, context.resourceId available
        const { data, error } = await context.client
          .from("xxx_table")
          .update({ name: input.name })
          .eq("id", context.resourceId)
          .select()
          .single();

        if (error) throw ServerErrors.database("Failed to update Xxx");

        return { success: true, message: "Xxx updated", xxx: data };
      });
  })
  .resolvers();
```

### Template: resource/ field resolver (ID from parent)

Field resolvers on a type (e.g. `DataModel.previewData`) get the resource ID from `parent`, not `args`. Use `({ parent })` in the `getResourceId` callback:

```typescript
previewData: createResolver<DataModelResolvers, "previewData">()
  .use(withOrgResourceClient("data_model", ({ parent }) => parent.id, "read"))
  .resolve(async (parent, _args, context) => {
    // context.client for DB, context.authenticatedUser for Trino/JWT
    return executePreviewQuery(
      parent.org_id,
      parent.dataset_id,
      generateTableId("USER_MODEL", parent.id),
      context.authenticatedUser,
      parent.name,
    );
  }),
```

Similarly for org-scoped field resolvers where the org ID comes from the parent:

```typescript
run: createResolver<MaterializationResolvers, "run">()
  .use(withOrgScopedClient(({ parent }) => parent.org_id))
  .resolve(async (parent, _args, context) => {
    // context.orgId === parent.org_id
  }),
```

### Template: system/ resolver

```typescript
import { createResolver } from "@/app/api/v1/osograph/utils/resolver-builder";
import { withSystemClient } from "@/app/api/v1/osograph/utils/resolver-middleware";
import { ServerErrors } from "@/app/api/v1/osograph/utils/errors";

export const runScheduledJob = createResolver<
  MutationResolvers,
  "runScheduledJob"
>()
  .use(withSystemClient())
  .resolve(async (_, args, context) => {
    // context.client has full admin access
    // No context.authenticatedUser — system calls bypass user auth
    const { error } = await context.client
      .from("scheduled_jobs")
      .update({ last_run_at: new Date().toISOString() })
      .eq("id", args.jobId);

    if (error) throw ServerErrors.database("Failed to run job");

    return { success: true };
  });
```

---

## osolint Rules

These are enforced automatically by osolint in CI:

| Rule                     | Description                                                       |
| ------------------------ | ----------------------------------------------------------------- |
| `no-direct-admin-client` | No `createAdminClient()` in resolver files — use `context.client` |
| Tier isolation           | `organization/` uses only `withOrgScopedClient`, etc.             |

If you see a lint error like `no-direct-admin-client: createAdminClient() must not be called in resolver files`, replace the call with the appropriate tier middleware and use `context.client`.

---

## Common Gotchas

### 1. `withValidation` must come before access-control middleware

The access-control middleware often reads IDs from `args.input`. If `withValidation` runs first, `args.input` is typed and validated:

```typescript
// CORRECT
.use(withValidation(UpdateDataModelInputSchema()))
.use(withOrgResourceClient("data_model", ({ args }) => args.input.dataModelId, "write"))

// WRONG — args.input is untyped when access-control runs
.use(withOrgResourceClient("data_model", ({ args }) => args.input.dataModelId, "write"))
.use(withValidation(UpdateDataModelInputSchema()))
```

### 2. `authenticatedUser` is available in all non-system contexts

`OrgScopedContext`, `AuthenticatedClientContext`, and `ResourceScopedContext` all include `authenticatedUser`. `SystemContext` does not (system calls bypass user auth).

### 3. `context.client` replaces `createAdminClient()`

The Supabase admin client is created once by the middleware and placed on `context.client`. Do not call `createAdminClient()` again inside the resolver.

### 4. `withOrgScopedClient` returns `orgRole` — use it for role-based checks

```typescript
.resolve(async (_, args, context) => {
  const isAdmin = context.orgRole === "owner" || context.orgRole === "admin";
  // ...
})
```

### 5. `withOrgResourceClient` returns `permissionLevel`

```typescript
.resolve(async (_, args, context) => {
  const canWrite = context.permissionLevel !== "read";
  // ...
})
```

### 6. Field resolvers with no auth → plain function

Simple field mappings don't need the builder:

```typescript
// OK — no auth needed
id: (parent) => parent.id,
orgId: (parent) => parent.org_id,
createdAt: (parent) => parent.created_at,
```

### 7. `getOrgId` / `getResourceId` receive `{ parent, context, args }` — destructure what you need

```typescript
// Mutation: ID comes from args
withOrgScopedClient(({ args }) => args.input.orgId);
withOrgResourceClient("data_model", ({ args }) => args.input.dataModelId);

// Field resolver: ID comes from parent
withOrgScopedClient(({ parent }) => parent.org_id);
withOrgResourceClient("data_model", ({ parent }) => parent.id);

// WRONG — callback receives an object, not a bare value
withOrgScopedClient((args) => args.input.orgId); // args is { parent, context, args }
```

---

## Testing After Migration

1. **TypeScript:** `pnpm --filter frontend exec tsc --noEmit` — must have zero errors
2. **Lint:** `pnpm --filter frontend lint` — must have no `no-direct-admin-client` violations
3. **Verify context types:** In your resolver's `.resolve()` callback, hover over `context` in VS Code to confirm it shows the correct type (`OrgScopedContext`, `ResourceScopedContext`, etc.)
4. **Verify args narrowing:** After `withValidation(MySchema())`, hover over `args.input` to confirm it's typed from the schema (not `any`)
5. **Manual smoke test:** Run the resolver via the GraphQL playground or an integration test and verify auth errors are thrown for unauthenticated/unauthorized requests

---

## Key File Locations

| File                            | Purpose                                                          |
| ------------------------------- | ---------------------------------------------------------------- |
| `utils/resolver-middleware.ts`  | The 4 middleware factories + `withValidation`, `withLogging`     |
| `types/enhanced-context.ts`     | The 4 context types (branded)                                    |
| `utils/access-control.ts`       | Underlying access-control functions called by middleware         |
| `utils/resolver-builder.ts`     | `createResolver`, `createResolversCollection`, `Middleware` type |
| `types/generated/validation.ts` | Generated Zod schemas for all GraphQL inputs                     |
| `README.md`                     | Full reference guide for the resolver pattern                    |
