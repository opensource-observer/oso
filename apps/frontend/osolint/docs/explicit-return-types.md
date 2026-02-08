# explicit-return-types

Requires explicit return type annotations on GraphQL resolver functions with multi-statement bodies to ensure type safety.

## Rule Details

This rule enforces:

- Multi-statement functions must have explicit return type annotations
- Single-expression arrow functions are exempt (TypeScript infers types automatically)

## Examples

### Incorrect

```typescript
// Missing return type on multi-statement function
export const invitationMutations = {
  createInvitation: async (
    _: unknown,
    args: MutationCreateInvitationArgs,
    context: GraphQLContext,
  ) => {
    const invitation = await createInvitationInDb(args.input);
    return { invitation, message: "Created", success: true };
  },
};

// Missing return type on sync multi-statement function
export const notebookTypeResolvers = {
  Notebook: {
    displayName: (parent: NotebooksRow) => {
      const name = parent.notebook_name;
      return name.toUpperCase();
    },
  },
};
```

### Correct

```typescript
import type {
  MutationCreateInvitationArgs,
  CreateInvitationPayload,
} from "@/lib/graphql/generated/graphql";
import type { NotebooksRow } from "@/lib/types/schema";

// Explicit return type on multi-statement async function
export const invitationMutations = {
  createInvitation: async (
    _: unknown,
    args: MutationCreateInvitationArgs,
    context: GraphQLContext,
  ): Promise<CreateInvitationPayload> => {
    const invitation = await createInvitationInDb(args.input);
    return { invitation, message: "Created", success: true };
  },
};

// Explicit return type on sync multi-statement function
export const notebookTypeResolvers = {
  Notebook: {
    displayName: (parent: NotebooksRow): string => {
      const name = parent.notebook_name;
      return name.toUpperCase();
    },
  },
};

// Single-expression functions are exempt (type inferred)
export const notebookTypeResolvers = {
  Notebook: {
    name: (parent: NotebooksRow) => parent.notebook_name,
    createdAt: (parent: NotebooksRow) => parent.created_at.toISOString(),
  },
};
```

## Common Return Type Patterns

### Mutations

```typescript
createInvitation: async (...): Promise<CreateInvitationPayload> => { }
revokeInvitation: async (...): Promise<RevokeInvitationPayload> => { }
updateDataset: async (...): Promise<UpdateDatasetPayload> => { }
```

### Queries

```typescript
getDataset: async (...): Promise<DatasetsRow | null> => { }
listNotebooks: async (...): Promise<NotebooksConnection> => { }
```

### Type Resolvers (Async)

```typescript
owner: async (parent: DatasetsRow): Promise<UserProfilesRow> => {};
organization: async (parent: InvitationsRow): Promise<OrganizationsRow> => {};
```

### Type Resolvers (Sync Multi-statement)

```typescript
status: (parent: InvitationsRow): InvitationStatus => {
  if (parent.accepted_at) return InvitationStatus.ACCEPTED;
  return InvitationStatus.PENDING;
};
```

All types are auto-generated from GraphQL schema or database schema.

## Scope

This rule only applies to files in:

- `app/api/v1/osograph/schema/resolvers/system/`
- `app/api/v1/osograph/schema/resolvers/user/`
- `app/api/v1/osograph/schema/resolvers/organization/`
- `app/api/v1/osograph/schema/resolvers/resource/`
