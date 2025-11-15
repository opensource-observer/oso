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
Query → Auth Check → Validate Where Clause → parseWhereClause() → mergePredicates() → buildQuery() → Supabase (with count) → buildConnectionOrEmpty() → { edges, pageInfo, totalCount }
```

## Directory Structure

```
frontend/app/api/v1/osograph/
├── route.ts                   # Apollo Server setup
├── schema/
│   ├── graphql/               # SDL type definitions
│   │   ├── base.graphql       # Base types, PageInfo, enums, JSON scalar
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
    ├── resolver-helpers.ts    # Shared resolver utilities
    ├── query-builder.ts       # Builds Supabase queries from predicates
    └── where-parser.ts        # Parses GraphQL where input to predicates
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
  widgets(
    orgId: ID!
    where: JSON
    first: Int = 50
    after: String
  ): WidgetConnection!
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
import type {
  ConnectionArgs,
  FilterableConnectionArgs,
} from "@/app/api/v1/osograph/utils/pagination";
import {
  validateInput,
  createWhereSchema,
} from "@/app/api/v1/osograph/utils/validation";
import { parseWhereClause } from "@/app/api/v1/osograph/utils/where-parser";
import {
  buildQuery,
  mergePredicates,
} from "@/app/api/v1/osograph/utils/query-builder";
import type { QueryPredicate } from "@/app/api/v1/osograph/utils/query-builder";
import { ServerErrors } from "@/app/api/v1/osograph/utils/errors";

const WidgetWhereSchema = createWhereSchema("widgets");

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
      args: FilterableConnectionArgs & { orgId: string },
      context: GraphQLContext,
    ) => {
      const user = requireAuthentication(context.user);
      await requireOrgMembership(user.userId, args.orgId);

      // Validate where clause if provided
      const validatedWhere = args.where
        ? validateInput(WidgetWhereSchema, args.where)
        : undefined;

      const supabase = createAdminClient();
      const [start, end] = preparePaginationRange(args);

      // Build base predicate (system filters)
      const basePredicate: Partial<QueryPredicate<"widgets">> = {
        eq: [{ key: "org_id", value: args.orgId }],
        is: [{ key: "deleted_at", value: null }],
      };

      // Parse and merge user filters
      const userPredicate = validatedWhere
        ? parseWhereClause(validatedWhere)
        : undefined;

      const predicate = userPredicate
        ? mergePredicates(basePredicate, userPredicate)
        : basePredicate;

      // Build and execute query
      const {
        data: widgets,
        count,
        error,
      } = await buildQuery(supabase, "widgets", predicate, (query) =>
        query.range(start, end),
      );

      if (error) {
        throw ServerErrors.database(
          `Failed to fetch widgets: ${error.message}`,
        );
      }

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

## Filtering with Where Clauses

List queries support flexible filtering via the `where` parameter, which accepts a JSON object specifying field-level filters.

### Filter Structure

```json
{
  "field_name": { "operator": value },
  "another_field": { "operator": value }
}
```

Multiple operators can be applied to the same field:

```json
{
  "created_at": {
    "gte": "2024-01-01T00:00:00Z",
    "lt": "2024-12-31T23:59:59Z"
  }
}
```

### Supported Operators

| Operator | Description                      | Example                                     |
| -------- | -------------------------------- | ------------------------------------------- |
| `eq`     | Equals                           | `{ "status": { "eq": "active" } }`          |
| `neq`    | Not equals                       | `{ "status": { "neq": "deleted" } }`        |
| `gt`     | Greater than                     | `{ "count": { "gt": 100 } }`                |
| `gte`    | Greater than or equal            | `{ "created_at": { "gte": "2024-01-01" } }` |
| `lt`     | Less than                        | `{ "count": { "lt": 1000 } }`               |
| `lte`    | Less than or equal               | `{ "updated_at": { "lte": "2024-12-31" } }` |
| `in`     | In array                         | `{ "id": { "in": ["id1", "id2", "id3"] } }` |
| `like`   | Pattern match (case-sensitive)   | `{ "name": { "like": "%search%" } }`        |
| `ilike`  | Pattern match (case-insensitive) | `{ "email": { "ilike": "%@example.com" } }` |
| `is`     | Null/boolean check               | `{ "deleted_at": { "is": null } }`          |

**Notes:**

- `like` and `ilike` use SQL wildcards: `%` (any characters), `_` (single character)
- `in` accepts an array of values
- `is` accepts `null` or boolean values

### GraphQL Query Examples

**Filter by name pattern:**

```graphql
query {
  notebooks(where: { notebook_name: { like: "%churn%" } }) {
    edges {
      node {
        id
        notebookName
      }
    }
  }
}
```

**Filter by date range:**

```graphql
query {
  datasets(
    where: {
      created_at: { gte: "2024-01-01T00:00:00Z", lt: "2024-12-31T23:59:59Z" }
    }
  ) {
    edges {
      node {
        id
        name
        createdAt
      }
    }
  }
}
```

**Multiple field filters:**

```graphql
query {
  dataModels(
    where: {
      name: { ilike: "%user%" }
      is_enabled: { eq: true }
      created_at: { gte: "2024-01-01T00:00:00Z" }
    }
  ) {
    edges {
      node {
        id
        name
        isEnabled
      }
    }
  }
}
```

**Combine with pagination:**

```graphql
query {
  notebooks(
    where: { notebook_name: { like: "%analysis%" } }
    first: 20
    after: "cursor123"
  ) {
    edges {
      node {
        id
        notebookName
      }
      cursor
    }
    pageInfo {
      hasNextPage
      endCursor
    }
    totalCount
  }
}
```

### Resolver Implementation Pattern

**1. Add where parameter to schema:**

```graphql
extend type Query {
  widgets(
    orgId: ID!
    where: JSON
    first: Int = 50
    after: String
  ): WidgetConnection!
}
```

**2. Create validation schema:**

```typescript
import { createWhereSchema } from "@/app/api/v1/osograph/utils/validation";

const WidgetWhereSchema = createWhereSchema("widgets");
```

**3. Implement filtering in resolver:**

```typescript
import { validateInput } from "@/app/api/v1/osograph/utils/validation";
import { parseWhereClause } from "@/app/api/v1/osograph/utils/where-parser";
import {
  buildQuery,
  mergePredicates,
} from "@/app/api/v1/osograph/utils/query-builder";
import type { QueryPredicate } from "@/app/api/v1/osograph/utils/query-builder";
import type { FilterableConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";

widgets: async (
  _: unknown,
  args: FilterableConnectionArgs & { orgId: string },
  context: GraphQLContext,
) => {
  const user = requireAuthentication(context.user);
  await requireOrgMembership(user.userId, args.orgId);

  // 1. Validate where clause
  const validatedWhere = args.where
    ? validateInput(WidgetWhereSchema, args.where)
    : undefined;

  const [start, end] = preparePaginationRange(args);

  // 2. Build base predicate (system filters)
  const basePredicate: Partial<QueryPredicate<"widgets">> = {
    eq: [{ key: "org_id", value: args.orgId }],
    is: [{ key: "deleted_at", value: null }],
  };

  // 3. Parse and merge user filters
  const userPredicate = validatedWhere
    ? parseWhereClause(validatedWhere)
    : undefined;

  const predicate = userPredicate
    ? mergePredicates(basePredicate, userPredicate)
    : basePredicate;

  // 4. Build and execute query
  const {
    data: widgets,
    count,
    error,
  } = await buildQuery(supabase, "widgets", predicate, (query) =>
    query.range(start, end),
  );

  if (error) {
    throw ServerErrors.database(`Failed to fetch widgets: ${error.message}`);
  }

  return buildConnectionOrEmpty(widgets, args, count);
};
```

### Security Considerations

**System filters are always enforced:**

```typescript
const basePredicate = {
  in: [{ key: "org_id", value: userOrgIds }], // ← Access control
  is: [{ key: "deleted_at", value: null }], // ← Soft delete filter
};
```

User-provided `where` filters are **merged** with system filters, ensuring:

- Users can only query resources in their organizations
- Soft-deleted resources are excluded
- Authorization checks are never bypassed

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

### Filtering

```typescript
// Validate and parse where clause
const validatedWhere = args.where
  ? validateInput(createWhereSchema("table_name"), args.where)
  : undefined;

const userPredicate = validatedWhere
  ? parseWhereClause(validatedWhere)
  : undefined;

// Merge with system filters
const basePredicate = {
  eq: [{ key: "org_id", value: orgId }],
  is: [{ key: "deleted_at", value: null }],
};

const predicate = userPredicate
  ? mergePredicates(basePredicate, userPredicate)
  : basePredicate;

// Build and execute query
const { data, count, error } = await buildQuery(
  supabase,
  "table_name",
  predicate,
  (query) => query.range(start, end),
);
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
- Validate where clauses: `validateInput(createWhereSchema("table"), args.where)`
- Merge predicates: Always combine user filters with system filters via `mergePredicates()`
- Use appropriate operators: Match filter operators to field types (dates with `gte`/`lte`, strings with `like`/`ilike`)
- Use type-safe query builder: `buildQuery()` for all filtered queries

**DON'T:**

- Skip auth checks
- Expose raw errors: use error helpers
- Hardcode pagination limits: use constants from `pagination.ts`
- Forget soft deletes
- Mix domain logic across resolvers
- Create custom connection types
- Skip input validation for mutations
- Apply user filters without validation
- Bypass system filters when merging predicates
- Use raw Supabase queries when filtering (use `buildQuery()` instead)
- Allow filtering on sensitive fields without proper authorization

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
