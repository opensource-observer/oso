# no-direct-admin-client

Blocks direct `createAdminClient` imports in `resolvers/system/`,
`resolvers/user/`, `resolvers/organization/`, and `resolvers/resource/` directories.

## Why

Enforces access control through validated helper functions instead of direct
database access.

## Use Instead

```typescript
// Bad
import { createAdminClient } from "@/lib/supabase/admin";

// Good (choose based on your directory)
import { getSystemClient } from "@/app/api/v1/osograph/utils/access-control";
import { getAuthenticatedClient } from "@/app/api/v1/osograph/utils/access-control";
import { getOrgScopedClient } from "@/app/api/v1/osograph/utils/access-control";
```

## Available Helpers

- `getSystemClient(context)` - System operations (use in `system/`)
- `getAuthenticatedClient(context)` - User-scoped operations (use in `user/`)
- `getOrgScopedClient(context, orgId)` - Org-scoped operations (use in
  `organization/`)
- `getOrgResourceClient(context, resourceType, resourceId)` - Org and
  resource-scoped operations (use in `resource/`)
