# no-inline-resolver-types

Prevents inline type annotations in GraphQL resolver parameters. Requires using generated types for consistency and type safety.

## Rule Details

This rule enforces:

- Parent parameters must use Row types from `@/lib/types/schema`
- Args parameters must use generated GraphQL types from `@/lib/graphql/generated/graphql`

## Examples

### Incorrect

```typescript
// Inline type for args parameter
export const invitationMutations = {
  createInvitation: async (
    _: unknown,
    args: { input: { orgId: string; email: string; role: string } },
    context: GraphQLContext,
  ) => {
    // ...
  },
};

// Inline type for parent parameter
export const notebookTypeResolvers = {
  Notebook: {
    name: (parent: { notebook_name: string }) => parent.notebook_name,
  },
};
```

### Correct

```typescript
import type { MutationCreateInvitationArgs } from "@/lib/graphql/generated/graphql";

// Using generated GraphQL type
export const invitationMutations = {
  createInvitation: async (
    _: unknown,
    args: MutationCreateInvitationArgs,
    context: GraphQLContext,
  ) => {
    // ...
  },
};

// Using Row type from schema
import { NotebooksRow } from "@/lib/types/schema";

export const notebookTypeResolvers = {
  Notebook: {
    name: (parent: NotebooksRow) => parent.notebook_name,
  },
};
```

## Common Type Mappings

### Args Types (Mutations)

- `createInvitation` → `MutationCreateInvitationArgs`
- `revokeInvitation` → `MutationRevokeInvitationArgs`
- `createDataset` → `MutationCreateDatasetArgs`
- `updateNotebook` → `MutationUpdateNotebookArgs`

### Args Types (Queries)

- `getDataset` → `QueryGetDatasetArgs`
- `listNotebooks` → `QueryListNotebooksArgs`

### Parent Types (from database)

- `Organization` → `OrganizationsRow`
- `Dataset` → `DatasetsRow`
- `Notebook` → `NotebooksRow`
- `Invitation` → `InvitationsRow`

All types are auto-generated from GraphQL schema or database schema.

## Scope

This rule only applies to files in:

- `app/api/v1/osograph/schema/resolvers/system/`
- `app/api/v1/osograph/schema/resolvers/user/`
- `app/api/v1/osograph/schema/resolvers/organization/`
- `app/api/v1/osograph/schema/resolvers/resource/`
