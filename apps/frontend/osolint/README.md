# OSO Frontend ESLint Rules

Custom ESLint rules for OSO.

## Structure

```
osolint/
├── index.mjs          # Plugin export
├── rules/
│   ├── access-control/
│   │   ├── no-direct-admin-client.mjs
│   │   └── enforce-access-tier-helpers.mjs
│   └── type-safety/
│       └── no-inline-resolver-types.mjs
└── docs/              # Rule documentation
```

## Rules

### `access-control/no-direct-admin-client`

Blocks `createAdminClient` imports in `resolvers/system/`, `resolvers/user/`,
`resolvers/organization/`, and `resolvers/resource/`.

**Use these helpers instead:**

- `getSystemClient(context)`: System operations
- `getAuthenticatedClient(context)`: User-scoped operations
- `getOrgScopedClient(context, orgId)`: Org-scoped operations
- `getOrgResourceClient(context, resourceType, resourceId, requiredPermission)`: Org resource access with permission overrides

### `access-control/enforce-access-tier-helpers`

Enforces strict tier separation: specific helpers per directory.

- `resolvers/system/`: Only `getSystemClient`
- `resolvers/user/`: Only `getAuthenticatedClient`
- `resolvers/organization/`: Only `getOrgScopedClient`
- `resolvers/resource/`: Only `getOrgResourceClient`

### `type-safety/no-inline-resolver-types`

Prevents inline type annotations (e.g., `parent: { field: string }`) in GraphQL resolver parent parameters.

**Instead, use Row types from `@/lib/types/schema-types`:**

```typescript
// Bad - inline type annotation
name: (parent: { notebook_name: string }) => parent.notebook_name;

// Good - proper Row type
import { NotebooksRow } from "@/lib/types/schema-types";
name: (parent: NotebooksRow) => parent.notebook_name;
```

**Benefits:**

- Type safety: Compile-time errors when schema changes
- Maintainability: Single source of truth
- Refactoring: IDE field renaming works across codebase

## Usage

```javascript
import osoFrontendRules from "./osolint/index.mjs";

export default {
  plugins: {
    "oso-frontend": osoFrontendRules,
  },
  rules: {
    "oso-frontend/access-control/no-direct-admin-client": "error",
    "oso-frontend/access-control/enforce-access-tier-helpers": "error",
    "oso-frontend/type-safety/no-inline-resolver-types": "error",
  },
};
```

## Adding Rules

1. Create rule file in `rules/<category>/`
2. Export in `index.mjs` with category prefix
3. Add documentation in `docs/`
4. Configure in `eslint.config.mjs`
