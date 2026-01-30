# enforce-access-tier-helpers

Enforces strict tier separation: each directory uses only its designated helper
function.

## Rules

**In `resolvers/system/`:**

- Allowed: `getSystemClient`
- Blocked: `getAuthenticatedClient`, `getOrgScopedClient`

**In `resolvers/user/`:**

- Allowed: `getAuthenticatedClient`
- Blocked: `getSystemClient`, `getOrgScopedClient`

**In `resolvers/organization/`:**

- Allowed: `getOrgScopedClient`
- Blocked: `getSystemClient`, `getAuthenticatedClient`

**In `resolvers/resource/`:**

- Allowed: `getOrgResourceClient`
- Blocked: `getSystemClient`, `getAuthenticatedClient`, `getOrgScopedClient`

## Examples

```typescript
// In resolvers/system/
import { getSystemClient } from "@/app/api/v1/osograph/utils/access-control";

// In resolvers/user/
import { getAuthenticatedClient } from "@/app/api/v1/osograph/utils/access-control";

// In resolvers/organization/
import { getOrgScopedClient } from "@/app/api/v1/osograph/utils/access-control";

// In resolvers/resource/
import { getOrgResourceClient } from "@/app/api/v1/osograph/utils/access-control";
```
