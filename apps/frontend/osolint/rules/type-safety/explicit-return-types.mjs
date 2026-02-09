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

/**
 * Checks if a function has a block body (multi-statement)
 * Returns false for single-expression arrow functions
 */
const hasBlockBody = (node) => node.body.type === AST_NODE_TYPES.BlockStatement;

/**
 * Checks if a function has an explicit return type annotation
 */
const hasReturnType = (node) => node.returnType !== undefined;

export default createRule({
  name: "explicit-return-types",
  meta: {
    type: "problem",
    docs: {
      description:
        "Require explicit return type annotations on GraphQL resolver functions with multi-statement bodies to ensure type safety.",
    },
    messages: {
      missingReturnType:
        "GraphQL resolver functions with multi-statement bodies must have an explicit return type annotation. Use Promise<PayloadType> for async resolvers or the direct type for sync resolvers. Examples: Promise<CreateInvitationPayload>, Promise<NotebooksRow | null>, string",
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

    const checkFunction = (node) => {
      if (!isResolverFunction(node)) {
        return;
      }

      // Exempt single-expression arrow functions (type inference is idiomatic)
      if (!hasBlockBody(node)) {
        return;
      }

      // Report if no return type annotation
      if (!hasReturnType(node)) {
        context.report({
          node,
          messageId: "missingReturnType",
        });
      }
    };

    return {
      ArrowFunctionExpression: checkFunction,
      FunctionExpression: checkFunction,
    };
  },
});
