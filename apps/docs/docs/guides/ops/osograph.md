---
title: OSO Graph API
sidebar_position: 10
---

# OSO Graph API Operations Guide

Guide for adding queries and mutations to OSOGraph.

# Schema & Resolver Architecture

The API follows **Relay's cursor-based pagination spec**. Every list query returns a Connection type.

**Key Principles:**

1. **Domain-Driven Schema**: Each resource has its own `.graphql` file in `schema/graphql/`. All files are merged at startup in `route.ts`.

2. **Connection Pattern**: All list queries return Connections, never arrays.

   ```
   Connection { edges: [{ node: T, cursor: String }], pageInfo: { ... }, totalCount: Int }
   ```

3. **Edge Types**: Edges wrap nodes with cursors. Define `{Type}Edge` and `{Type}Connection` for each resource.

4. **Field Resolvers**: Types can have field resolvers that load nested resources. These run lazily when the field is queried.

5. **Type Mapping**: Map database columns (`snake_case`) to GraphQL fields (`camelCase`) via field resolvers.

**Data Flow:**

```
Query → Auth Check → preparePaginationRange() → Supabase (with count) → buildConnectionOrEmpty() → { edges, pageInfo, totalCount }
```

## Directory Structure

```
frontend/app/api/v1/osograph/
├── route.ts                   # Apollo Server setup
├── schema/
│   ├── graphql/               # SDL type definitions
│   │   ├── base.graphql       # Base types, PageInfo, enums
│   │   └── *.graphql          # Domain schemas
│   └── resolvers/             # Resolver implementations
│       ├── index.ts           # Combines all resolvers
│       └── *.ts               # Domain resolvers
├── types/
│   └── context.ts             # GraphQL context
└── utils/
    ├── auth.ts                # Auth helpers
    ├── errors.ts              # Error helpers
    ├── pagination.ts          # Cursor pagination (constants & encoding)
    ├── connection.ts          # Connection builder
    ├── validation.ts          # Zod schemas & input validation
    └── resolver-helpers.ts    # Shared resolver utilities
```

## Adding a Query

### Example: Widget Resource

**1. Define Schema** (`schema/graphql/widget.graphql`)

```graphql
type Widget {
  id: ID!
  name: String!
  orgId: ID!
  createdAt: DateTime!
  organization: Organization!
}

type WidgetEdge {
  node: Widget!
  cursor: String!
}

type WidgetConnection {
  edges: [WidgetEdge!]!
  pageInfo: PageInfo!
  totalCount: Int
}

extend type Query {
  widget(id: ID!): Widget
  widgets(orgId: ID!, first: Int = 50, after: String): WidgetConnection!
}
```

**Note:** The default value `50` matches the `DEFAULT_PAGE_SIZE` constant in `utils/pagination.ts`. Maximum allowed is `MAX_PAGE_SIZE = 100`.

**2. Implement Resolver** (`schema/resolvers/widget.ts`)

```typescript
import { createAdminClient } from "@/lib/supabase/admin";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import {
  requireAuthentication,
  requireOrgMembership,
} from "@/app/api/v1/osograph/utils/auth";
import {
  buildConnectionOrEmpty,
  preparePaginationRange,
} from "@/app/api/v1/osograph/utils/resolver-helpers";
import type { ConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";

export const widgetResolvers = {
  Query: {
    widget: async (
      _: unknown,
      args: { id: string },
      context: GraphQLContext,
    ) => {
      const user = requireAuthentication(context.user);
      const supabase = createAdminClient();

      const { data: widget } = await supabase
        .from("widgets")
        .select("*")
        .eq("id", args.id)
        .is("deleted_at", null)
        .single();

      if (!widget) return null;

      await requireOrgMembership(user.userId, widget.org_id);
      return widget;
    },

    widgets: async (
      _: unknown,
      args: ConnectionArgs & { orgId: string },
      context: GraphQLContext,
    ) => {
      const user = requireAuthentication(context.user);
      await requireOrgMembership(user.userId, args.orgId);

      const supabase = createAdminClient();
      const [start, end] = preparePaginationRange(args);

      const { data: widgets, count } = await supabase
        .from("widgets")
        .select("*", { count: "exact" })
        .eq("org_id", args.orgId)
        .is("deleted_at", null)
        .range(start, end);

      return buildConnectionOrEmpty(widgets, args, count);
    },
  },

  Widget: {
    orgId: (parent: { org_id: string }) => parent.org_id,
    createdAt: (parent: { created_at: string }) => parent.created_at,

    organization: async (parent: { org_id: string }) => {
      const supabase = createAdminClient();
      const { data: org } = await supabase
        .from("organizations")
        .select("*")
        .eq("id", parent.org_id)
        .single();
      return org;
    },
  },
};
```

**3. Register**

Schema files (`.graphql`) are **automatically discovered** by `route.ts`.

Add resolver to `schema/resolvers/index.ts`:

```typescript
import { widgetResolvers } from "./widget";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";

export const resolvers: GraphQLResolverMap<GraphQLContext> = {
  Query: {
    ...viewerResolvers.Query,
    ...widgetResolvers.Query,
    // ... other resolvers
  },

  Mutation: {
    ...widgetResolvers.Mutation,
    // ... other resolvers
  },

  Widget: widgetResolvers.Widget,
  // ... other type resolvers
};
```

## Adding a Mutation

**1. Define Schema** (`schema/graphql/widget.graphql`)

```graphql
input CreateWidgetInput {
  orgId: ID!
  name: String!
}

type CreateWidgetPayload {
  success: Boolean!
  widget: Widget
  message: String
}

extend type Mutation {
  createWidget(input: CreateWidgetInput!): CreateWidgetPayload!
}
```

**2. Create Validation Schema** (`utils/validation.ts`)

```typescript
import { z } from "zod";

export const CreateWidgetSchema = z.object({
  orgId: z.string().uuid("Invalid organization ID"),
  name: z.string().min(1, "Widget name is required"),
});
```

**3. Implement Resolver** (`schema/resolvers/widget.ts`)

```typescript
import { validateInput } from "@/app/api/v1/osograph/utils/validation";
import { CreateWidgetSchema } from "@/app/api/v1/osograph/utils/validation";
import { ServerErrors } from "@/app/api/v1/osograph/utils/errors";

Mutation: {
  createWidget: async (
    _: unknown,
    args: { input: { orgId: string; name: string } },
    context: GraphQLContext,
  ) => {
    const user = requireAuthentication(context.user);
    const input = validateInput(CreateWidgetSchema, args.input);
    await requireOrgMembership(user.userId, input.orgId);

    const supabase = createAdminClient();

    const { data: widget, error } = await supabase
      .from("widgets")
      .insert({
        org_id: input.orgId,
        name: input.name,
        created_by: user.userId,
      })
      .select()
      .single();

    if (error) throw ServerErrors.database(error.message);

    return { success: true, widget, message: "Widget created successfully" };
  },
}
```

**4. Register**

Add to `schema/resolvers/index.ts`:

```typescript
export const resolvers: GraphQLResolverMap<GraphQLContext> = {
  Mutation: {
    ...widgetResolvers.Mutation,
    // ... other mutations
  },
};
```

Export the validation schema in `utils/validation.ts` so it's available for import.

## Patterns

### Pagination

```typescript
const [start, end] = preparePaginationRange(args); // Get offset range
const { data, count } = await supabase
  .from("t")
  .select("*", { count: "exact" })
  .range(start, end);
return buildConnectionOrEmpty(data, args, count); // Build connection
```

### Field Mapping

```typescript
Widget: {
  orgId: (parent: { org_id: string }) => parent.org_id,
}
```

### Nested Resources

```typescript
Widget: {
  organization: async (parent: { org_id: string }) => {
    return getOrganization(parent.org_id);
  },
}
```

## Best Practices

**DO:**

- Authenticate first: `requireAuthentication(context.user)`
- Check org membership: `requireOrgMembership(userId, orgId)`
- Use error helpers: `ResourceErrors.notFound()`, `ValidationErrors.invalidInput()`
- Soft delete: `.is("deleted_at", null)`
- Return connections for lists: `buildConnectionOrEmpty(items, args, count)`
- Map DB columns: `orgId: (p) => p.org_id`
- Return structured payloads: `{ success, resource, message }`
- Fetch counts for pagination: `.select("*", { count: "exact" })`
- Use validation schemas: `validateInput(Schema, input)`

**DON'T:**

- Skip auth checks
- Expose raw errors: use error helpers
- Hardcode pagination limits: use constants from `pagination.ts`
- Forget soft deletes
- Mix domain logic across resolvers
- Create custom connection types
- Skip input validation for mutations

**Naming:**

- Queries: `resource`, `resources`
- Mutations: `createResource`, `updateResource`
- Input: `{Action}{Resource}Input`
- Payload: `{Action}{Resource}Payload`

## Error Helpers

```typescript
// Auth
AuthenticationErrors.notAuthenticated();
AuthenticationErrors.notAuthorized();

// Resources
ResourceErrors.notFound("Widget", id);
ResourceErrors.alreadyExists("Widget", name);

// Validation
ValidationErrors.invalidInput("field", "reason");
ValidationErrors.missingField("field");

// Server
ServerErrors.database(message);
ServerErrors.internal(message);
```

## Debugging

- Apollo Sandbox: `/api/v1/graphql` (change graph URL to `/api/v1/osograph`)
- Error stack traces: enabled in `dev`
- Check schema loading: verify file in `schemaFiles` array
