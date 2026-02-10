import { ESLintUtils } from "@typescript-eslint/utils";
import { AST_NODE_TYPES } from "@typescript-eslint/utils";
import path from "node:path";

const createRule = ESLintUtils.RuleCreator(
  (name) =>
    `https://github.com/opensource-observer/oso/blob/main/apps/frontend/osolint/docs/${name}.md`,
);

const RESOLVER_BASE = "app/api/v1/osograph/schema/resolvers/";
const MANAGED_DIRS = ["system/", "user/", "organization/", "resource/"];

const normalizePath = (filename) => filename.split(path.sep).join("/");

const isInManagedDir = (normalizedPath) =>
  normalizedPath.includes(RESOLVER_BASE) &&
  MANAGED_DIRS.some((dir) => normalizedPath.includes(RESOLVER_BASE + dir));

/**
 * Checks if a parameter has an inline type annotation (object type literal)
 */
const hasInlineObjectType = (param) => {
  if (!param.typeAnnotation) return false;

  const typeAnnotation = param.typeAnnotation.typeAnnotation;

  // Check for inline object types like { field: string }
  if (typeAnnotation.type === AST_NODE_TYPES.TSTypeLiteral) {
    return true;
  }

  return false;
};

/**
 * Checks if this is a resolver function based on context
 * Must be:
 * 1. Inside a resolver object (e.g., Notebook: { ... })
 * 2. An arrow function or function expression
 * 3. First parameter should be "parent", "_parent", "_", or "_root"
 */
const isResolverFunction = (node) => {
  // Must be an arrow function or function expression
  if (
    node.type !== AST_NODE_TYPES.ArrowFunctionExpression &&
    node.type !== AST_NODE_TYPES.FunctionExpression
  ) {
    return false;
  }

  // Must have at least one parameter
  if (!node.params || node.params.length === 0) {
    return false;
  }

  const firstParam = node.params[0];

  // First parameter should be named "parent", "_parent", "_", or "_root"
  if (firstParam.type !== AST_NODE_TYPES.Identifier) {
    return false;
  }

  const paramName = firstParam.name;
  if (
    paramName !== "parent" &&
    paramName !== "_parent" &&
    paramName !== "_" &&
    paramName !== "_root"
  ) {
    return false;
  }

  return true;
};

export default createRule({
  name: "no-inline-resolver-types",
  meta: {
    type: "problem",
    docs: {
      description:
        "Prevent inline type annotations in resolver parameters. Use generated GraphQL types for args (e.g., MutationCreateInvitationArgs) and Row types from @/lib/types/schema for parent parameters.",
    },
    messages: {
      noInlineTypeParent:
        "Inline type annotations like '{{ field: string }}' are not allowed for resolver parent parameters. Import and use the appropriate Row type from '@/lib/types/schema' (e.g., NotebooksRow, DatasetsRow, ModelRow).",
      noInlineTypeArgs:
        "Inline type annotations like '{{ input: {{ field: string }} }}' are not allowed for resolver args parameters. Import and use the appropriate generated GraphQL type from '@/lib/graphql/generated/graphql' (e.g., MutationCreateInvitationArgs, QueryGetDatasetArgs).",
    },
    schema: [],
  },
  defaultOptions: [],

  create(context) {
    const filename = context.filename ?? context.getFilename();
    const normalizedPath = normalizePath(filename);

    // Only check files in managed resolver directories
    if (!isInManagedDir(normalizedPath)) {
      return {};
    }

    return {
      ArrowFunctionExpression(node) {
        if (!isResolverFunction(node)) {
          return;
        }

        // Check first parameter (parent)
        const firstParam = node.params[0];
        if (hasInlineObjectType(firstParam)) {
          context.report({
            node: firstParam.typeAnnotation,
            messageId: "noInlineTypeParent",
          });
        }

        // Check second parameter (args) if it exists
        if (node.params.length >= 2) {
          const secondParam = node.params[1];
          if (hasInlineObjectType(secondParam)) {
            context.report({
              node: secondParam.typeAnnotation,
              messageId: "noInlineTypeArgs",
            });
          }
        }
      },
      FunctionExpression(node) {
        if (!isResolverFunction(node)) {
          return;
        }

        // Check first parameter (parent)
        const firstParam = node.params[0];
        if (hasInlineObjectType(firstParam)) {
          context.report({
            node: firstParam.typeAnnotation,
            messageId: "noInlineTypeParent",
          });
        }

        // Check second parameter (args) if it exists
        if (node.params.length >= 2) {
          const secondParam = node.params[1];
          if (hasInlineObjectType(secondParam)) {
            context.report({
              node: secondParam.typeAnnotation,
              messageId: "noInlineTypeArgs",
            });
          }
        }
      },
    };
  },
});
