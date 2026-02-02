import noDirectAdminClient from "./rules/access-control/no-direct-admin-client.mjs";
import enforceAccessTierHelpers from "./rules/access-control/enforce-access-tier-helpers.mjs";

export default {
  rules: {
    "access-control/no-direct-admin-client": noDirectAdminClient,
    "access-control/enforce-access-tier-helpers": enforceAccessTierHelpers,
  },
};
