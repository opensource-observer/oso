import { ESLintUtils } from "@typescript-eslint/utils";
import path from "node:path";

const createRule = ESLintUtils.RuleCreator(
  (name) =>
    `https://github.com/opensource-observer/oso/blob/main/apps/frontend/osolint/docs/${name}.md`,
);

const RESOLVER_BASE = "app/api/v1/osograph/schema/resolvers/";
const ACCESS_CONTROL_IMPORTS = new Set([
  "@/app/api/v1/osograph/utils/access-control",
  "@/app/api/v1/osograph/utils/access-control.ts",
]);

const TIER_CONFIG = {
  system: {
    allowed: new Set(["getSystemClient"]),
    messageId: "wrongHelperInSystem",
  },
  user: {
    allowed: new Set(["getAuthenticatedClient"]),
    messageId: "wrongHelperInUser",
  },
  organization: {
    allowed: new Set(["getOrgScopedClient"]),
    messageId: "wrongHelperInOrganization",
  },
  resource: {
    allowed: new Set(["getOrgResourceClient"]),
    messageId: "wrongHelperInResource",
  },
};

const ALL_HELPERS = new Set(
  Object.values(TIER_CONFIG).flatMap((config) => [...config.allowed]),
);

const normalizePath = (filename) => filename.split(path.sep).join("/");

const detectTier = (normalizedPath) =>
  Object.keys(TIER_CONFIG).find((tier) =>
    normalizedPath.includes(`${RESOLVER_BASE}${tier}/`)
  );

const isAccessControlImport = (node) =>
  node.source.type === "Literal" &&
  ACCESS_CONTROL_IMPORTS.has(node.source.value);

const getImportedHelpers = (node) =>
  node.specifiers
    .filter(
      (spec) =>
        spec.type === "ImportSpecifier" &&
        spec.imported.type === "Identifier" &&
        ALL_HELPERS.has(spec.imported.name),
    )
    .map((spec) => ({
      name: spec.imported.name,
      node: spec,
    }));

export default createRule({
  name: "enforce-access-tier-helpers",
  meta: {
    type: "problem",
    docs: {
      description:
        "Enforce access tier separation - each directory uses only its designated helper",
    },
    messages: {
      wrongHelperInSystem:
        "'{{helper}}' cannot be used in resolvers/system/ directory. Use getSystemClient instead.",
      wrongHelperInUser:
        "'{{helper}}' cannot be used in resolvers/user/ directory. Use getAuthenticatedClient instead.",
      wrongHelperInOrganization:
        "'{{helper}}' cannot be used in resolvers/organization/ directory. Use getOrgScopedClient instead.",
      wrongHelperInResource:
        "'{{helper}}' cannot be used in resolvers/resource/ directory. Use getOrgResourceClient instead.",
    },
    schema: [],
  },
  defaultOptions: [],

  create(context) {
    const filename = context.filename ?? context.getFilename();
    const normalizedPath = normalizePath(filename);
    const tier = detectTier(normalizedPath);

    if (!tier) return {};

    const { allowed, messageId } = TIER_CONFIG[tier];

    return {
      ImportDeclaration(node) {
        if (!isAccessControlImport(node)) return;

        getImportedHelpers(node).forEach(({ name, node: specNode }) => {
          if (!allowed.has(name)) {
            context.report({
              node: specNode,
              messageId,
              data: { helper: name },
            });
          }
        });
      },
    };
  },
});
