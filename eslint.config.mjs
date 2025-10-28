import { defineConfig, globalIgnores } from "eslint/config";
import { includeIgnoreFile } from "@eslint/compat";
import { fileURLToPath } from "node:url";

import globals from "globals";
import tsParser from "@typescript-eslint/parser";
import unusedImports from "eslint-plugin-unused-imports";
import typescriptEslint from "@typescript-eslint/eslint-plugin";
import react from "eslint-plugin-react";
import eslint from "@eslint/js";

import { FlatCompat } from "@eslint/eslintrc";

const gitignorePath = fileURLToPath(new URL(".gitignore", import.meta.url));

const compat = new FlatCompat({
    baseDirectory: new URL(".", import.meta.url).pathname,
    recommendedConfig: eslint.configs.recommended,
    allConfig: eslint.configs.all,
});

export default defineConfig([
    includeIgnoreFile(gitignorePath),
    globalIgnores([
        "**/.venv/**",
        "**/.pytest_cache/**",
        "**/.ruff_cache/**",
        "**/vendor/*.js",
        "vendor/**/*.js",
        "**/test.only/**",
        "**/utilities/**",
        "**/postcss.config.js",
        "!**/.storybook",
        // Workspaces with their own ESLint configs handle their own linting
        "apps/frontend/**",
        "apps/docs/**",
        // Config files don't need type-aware linting
        "**/*.mjs",
    ]),
    eslint.configs.recommended,
    ...compat.extends(
        "plugin:@typescript-eslint/recommended",
        // "plugin:@typescript-eslint/recommended-type-checked",
        // "plugin:@typescript-eslint/strict",
        // "plugin:@typescript-eslint/strict-type-checked",
        "plugin:react/recommended",
        "prettier",
    ),
    {
        files: ["**/*.{js,cjs,jsx,ts,tsx}"],

        languageOptions: {
            globals: {
                ...globals.browser,
                ...globals.es2021,
                ...globals.node,
            },

            parser: tsParser,
            ecmaVersion: "latest",
            sourceType: "module",

            parserOptions: {
                ecmaFeatures: {
                    jsx: true,
                },
                project: true,
            },
        },

        plugins: {
            "unused-imports": unusedImports,
            "@typescript-eslint": typescriptEslint,
            react,
        },

        settings: {
            react: {
                version: "detect",
            },
        },

        rules: {
            "@typescript-eslint/no-misused-promises": "error",
            "@typescript-eslint/no-floating-promises": "error",
            "@typescript-eslint/no-explicit-any": "off",
            "@typescript-eslint/no-unused-expressions": "off",
            "@typescript-eslint/no-unused-vars": "off",
            "unused-imports/no-unused-imports": "error",

            "unused-imports/no-unused-vars": ["warn", {
                vars: "all",
                varsIgnorePattern: "^_",
                args: "after-used",
                argsIgnorePattern: "^_",
            }],

            "no-restricted-properties": ["error", {
                object: "console",
                property: "error",
                message: "Please use the logger instead.",
            }],

            "no-restricted-globals": ["error", {
                name: "prompt",
                message: "Please use a React modal instead.",
            }],

            "react/react-in-jsx-scope": "off",
            "react/prop-types": "off",
            "react/no-unknown-property": ["error", {
                ignore: ["tw", "cmdk-input-wrapper"],
            }],
        },
    },
]);
