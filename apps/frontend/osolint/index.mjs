import noDirectAdminClient from "./rules/access-control/no-direct-admin-client.mjs";
import enforceAccessTierHelpers from "./rules/access-control/enforce-access-tier-helpers.mjs";
import noInlineResolverTypes from "./rules/type-safety/no-inline-resolver-types.mjs";

export default {
  rules: {
    "access-control/no-direct-admin-client": noDirectAdminClient,
    "access-control/enforce-access-tier-helpers": enforceAccessTierHelpers,
    "type-safety/no-inline-resolver-types": noInlineResolverTypes,
  },
};
