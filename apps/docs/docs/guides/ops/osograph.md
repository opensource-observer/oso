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
│   ├── context.ts             # GraphQL context
│   └── utils.ts               # Type utilities
└── utils/
    ├── auth.ts                # Auth helpers
    ├── connection.ts          # Connection builder
    ├── errors.ts              # Error helpers
    ├── pagination.ts          # Cursor pagination (constants & encoding)
    ├── query-builder.ts       # Builds Supabase queries from predicates
    ├── query-helpers.ts       # High-level query helpers (queryWithPagination)
    ├── resolver-helpers.ts    # Shared resolver utilities
    ├── validation.ts          # Zod schemas & input validation
    └── where-parser.ts        # Parses GraphQL where input to predicates
```

## Adding a Query

### Example: Widget Resource

**1. Define Schema** (`schema/graphql/widget.graphql`)

````graphql
type Widget {
  id: ID!
  name: String!
  orgId: ID!
  createdAt: DateTime!
  updatedAt: DateTime!
  creatorId: ID!
  creator: User!
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
  """
  Query widgets with optional filtering and pagination.

  The where parameter accepts a JSON object with field-level filtering.
  Each field can have comparison operators: eq, neq, gt, gte, lt, lte, in, like, ilike, is.

  Example:
  ```json
  {
    "name": { "like": "%search%" },
    "created_at": { "gte": "2024-01-01T00:00:00Z" }
  }
  ```
  """
  widgets(where: JSON, first: Int = 50, after: String): WidgetConnection!
}
````

:::tip
To query a single widget, use filtering:

```graphql
widgets(where: { id: { eq: "widget_id" } })
```

:::

**2. Implement Resolver** (`schema/resolvers/widget.ts`)

```typescript
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import {
  getOrganization,
  getUserProfile,
} from "@/app/api/v1/osograph/utils/auth";
import type { FilterableConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import { createWhereSchema } from "@/app/api/v1/osograph/utils/validation";
import { queryWithPagination } from "@/app/api/v1/osograph/utils/query-helpers";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";

const WidgetWhereSchema = createWhereSchema("widgets");

export const widgetResolvers: GraphQLResolverModule<GraphQLContext> = {
  Query: {
    widgets: async (
      _: unknown,
      args: FilterableConnectionArgs,
      context: GraphQLContext,
    ) => {
      return queryWithPagination(args, context, {
        tableName: "widgets",
        whereSchema: WidgetWhereSchema,
        requireAuth: true,
        filterByUserOrgs: true,
        basePredicate: {
          is: [{ key: "deleted_at", value: null }],
        },
      });
    },
  },

  Widget: {
    name: (parent: { widget_name: string }) => parent.widget_name,
    orgId: (parent: { org_id: string }) => parent.org_id,
    createdAt: (parent: { created_at: string }) => parent.created_at,
    updatedAt: (parent: { updated_at: string }) => parent.updated_at,
    creatorId: (parent: { created_by: string }) => parent.created_by,

    creator: async (parent: { created_by: string }) => {
      return getUserProfile(parent.created_by);
    },

    organization: async (parent: { org_id: string }) => {
      return getOrganization(parent.org_id);
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

:::warning
Field names in `where` filters **must use snake_case** (database column names), not camelCase (GraphQL field names). This is a known limitation due to the current 1:1 mapping with Supabase.

For example, use `notebook_name` instead of `notebookName`, and `created_at` instead of `createdAt`.
:::

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

:::note

- `like` and `ilike` use SQL wildcards: `%` (any characters), `_` (single character)
- `in` accepts an array of values
- `is` accepts `null` or boolean values
  :::

### GraphQL Query Examples

**Single resource by ID:**

```graphql
query {
  notebooks(where: { id: { eq: "123e4567-e89b-12d3-a456-426614174000" } }) {
    edges {
      node {
        id
        name
      }
    }
  }
}
```

**Filter by name pattern:**

```graphql
query {
  notebooks(where: { notebook_name: { like: "%churn%" } }) {
    edges {
      node {
        id
        name
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
        name
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

### Using the `queryWithPagination` Helper

For the common use case of querying a single table with pagination, filtering, and org-scoped access control, use the `queryWithPagination` helper. This abstracts away all the boilerplate of validating where clauses, building predicates, and executing queries.

**1. Schema is already defined** (from the example above - no additional parameters needed)

The `where` parameter provides flexible filtering, eliminating the need for separate singular and plural queries.

**2. Create validation schema:**

```typescript
import { createWhereSchema } from "@/app/api/v1/osograph/utils/validation";

const WidgetWhereSchema = createWhereSchema("widgets");
```

**3. Use the helper in your resolver:**

```typescript
import { queryWithPagination } from "@/app/api/v1/osograph/utils/query-helpers";
import type { FilterableConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";

widgets: async (
  _: unknown,
  args: FilterableConnectionArgs,
  context: GraphQLContext,
) => {
  return queryWithPagination(args, context, {
    tableName: "widgets",
    whereSchema: WidgetWhereSchema,
    requireAuth: true,
    filterByUserOrgs: true,
    basePredicate: {
      is: [{ key: "deleted_at", value: null }],
    },
  });
};
```

**Helper Options:**

| Option             | Type                 | Description                                                               |
| ------------------ | -------------------- | ------------------------------------------------------------------------- |
| `tableName`        | `string`             | The database table to query                                               |
| `whereSchema`      | `ZodSchema`          | Validation schema for the where clause                                    |
| `requireAuth`      | `boolean`            | Whether to require authentication                                         |
| `filterByUserOrgs` | `boolean`            | If `true`, automatically filters by user's org memberships                |
| `parentOrgIds`     | `string \| string[]` | Specific org ID(s) to filter by (used when `filterByUserOrgs` is `false`) |
| `basePredicate`    | `QueryPredicate`     | Additional system filters (e.g., soft delete, status checks)              |
| `errorMessage`     | `string`             | Optional custom error message                                             |

**Examples:**

Top-level user resources:

```typescript
// Query all resources the authenticated user can access
return queryWithPagination(args, context, {
  tableName: "notebooks",
  whereSchema: NotebookWhereSchema,
  requireAuth: true,
  filterByUserOrgs: true, // ← Automatically scopes to user's orgs
  basePredicate: {
    is: [{ key: "deleted_at", value: null }],
  },
});
```

Nested resources in field resolvers:

```typescript
// In Dataset type resolver
dataModels: async (parent: { id: string; org_id: string }, args, context) => {
  return queryWithPagination(args, context, {
    tableName: "model",
    whereSchema: DataModelWhereSchema,
    requireAuth: false,
    filterByUserOrgs: false,
    parentOrgIds: parent.org_id, // ← Use parent's org_id
    basePredicate: {
      is: [{ key: "deleted_at", value: null }],
      eq: [{ key: "dataset_id", value: parent.id }],
    },
  });
};
```

The helper automatically handles:

- Authentication (if `requireAuth` is `true`)
- Organization access validation
- Where clause validation and parsing
- Predicate merging (system filters + user filters)
- Query building and execution
- Connection building with pagination
- Error handling

### Security Considerations

:::warning
System filters (access control, soft deletes) are **always enforced** and cannot be bypassed by user-provided `where` filters.
:::

```typescript
const basePredicate = {
  in: [{ key: "org_id", value: userOrgIds }], // ← Access control
  is: [{ key: "deleted_at", value: null }], // ← Soft delete filter
};
```

User-provided `where` filters are **merged** with system filters using `mergePredicates()`, ensuring:

- Users can only query resources in their organizations
- Soft-deleted resources are excluded
- Authorization checks are never bypassed

## Patterns

### Pagination & Filtering (Recommended)

For standard list queries with pagination and filtering, use the `queryWithPagination` helper:

```typescript
return queryWithPagination(args, context, {
  tableName: "table_name",
  whereSchema: TableWhereSchema,
  requireAuth: true,
  filterByUserOrgs: true,
  basePredicate: {
    is: [{ key: "deleted_at", value: null }],
  },
});
```

### Manual Pagination (for custom queries)

When you need more control (e.g., complex joins, custom logic):

```typescript
const [start, end] = preparePaginationRange(args);
const { data, count } = await supabase
  .from("t")
  .select("*", { count: "exact" })
  .range(start, end);
return buildConnectionOrEmpty(data, args, count);
```

### Manual Filtering (for custom queries)

When `queryWithPagination` doesn't fit your use case:

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

- Use `queryWithPagination` for standard list queries (pagination + filtering + org-scoping)
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
