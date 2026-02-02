import { ESLintUtils } from "@typescript-eslint/utils";
import path from "node:path";

const createRule = ESLintUtils.RuleCreator(
  (name) =>
    `https://github.com/opensource-observer/oso/blob/main/apps/frontend/osolint/docs/${name}.md`,
);

const RESOLVER_BASE = "app/api/v1/osograph/schema/resolvers/";
const MANAGED_DIRS = ["system/", "user/", "organization/", "resource/"];
const ALLOWED_FILES = new Set([
  "app/api/v1/osograph/utils/access-control.ts",
  "app/api/v1/osograph/utils/auth.ts",
  "app/api/v1/osograph/utils/resolver-helpers.ts",
  "app/api/v1/osograph/utils/query-helpers.ts",
]);

const normalizePath = (filename) => filename.split(path.sep).join("/");

const isInManagedDir = (normalizedPath) =>
  normalizedPath.includes(RESOLVER_BASE) &&
  MANAGED_DIRS.some((dir) => normalizedPath.includes(RESOLVER_BASE + dir));

const isAllowedFile = (normalizedPath) =>
  Array.from(ALLOWED_FILES).some((file) => normalizedPath.endsWith(file));

const importsCreateAdminClient = (node) =>
  node.source.type === "Literal" &&
  node.source.value === "@/lib/supabase/admin" &&
  node.specifiers.some(
    (spec) =>
      spec.type === "ImportSpecifier" &&
      spec.imported.type === "Identifier" &&
      spec.imported.name === "createAdminClient",
  );

export default createRule({
  name: "no-direct-admin-client",
  meta: {
    type: "problem",
    docs: {
      description:
        "Prevent direct use of createAdminClient in resolvers. Use access control helpers instead.",
    },
    messages: {
      noDirectAdminClient:
        "Direct use of createAdminClient is not allowed in resolvers. Use access control helpers from utils/access-control.ts instead (getSystemClient, getAuthenticatedClient, getOrgScopedClient, getOrgResourceClient).",
    },
    schema: [],
  },
  defaultOptions: [],

  create(context) {
    const filename = context.filename ?? context.getFilename();
    const normalizedPath = normalizePath(filename);

    if (isAllowedFile(normalizedPath) || !isInManagedDir(normalizedPath)) {
      return {};
    }

    return {
      ImportDeclaration(node) {
        if (importsCreateAdminClient(node)) {
          context.report({ node, messageId: "noDirectAdminClient" });
        }
      },
    };
  },
});
