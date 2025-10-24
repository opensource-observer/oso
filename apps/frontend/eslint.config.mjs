import { defineConfig } from "eslint/config";
import { includeIgnoreFile } from "@eslint/compat";
import noRelativeImportPaths from "eslint-plugin-no-relative-import-paths";
import tsParser from "@typescript-eslint/parser";
import path from "node:path";
import { fileURLToPath } from "node:url";
import js from "@eslint/js";
import { FlatCompat } from "@eslint/eslintrc";
import { fixupConfigRules } from "@eslint/compat";
import rootConfig from "../../eslint.config.mjs";
import { resolveFlatConfig } from "@leancodepl/resolve-eslint-flat-config";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const gitignorePath = fileURLToPath(new URL(".gitignore", import.meta.url));
const compat = new FlatCompat({
    baseDirectory: __dirname,
    recommendedConfig: js.configs.recommended,
    allConfig: js.configs.all,
});

export default defineConfig(resolveFlatConfig([
    ...rootConfig,
    includeIgnoreFile(gitignorePath),
    {
        ignores: ["lib/graphql/generated/**"],
    },
    ...fixupConfigRules(compat.extends(
        "next/core-web-vitals",
        "plugin:storybook/recommended",
    )),
    {
        files: ["*.mjs", "*.js"],
        rules: {
            "@typescript-eslint/no-misused-promises": "off",
            "@typescript-eslint/no-floating-promises": "off",
        },
    },
    {
        files: ["**/*.{ts,tsx}"],

        plugins: {
            "no-relative-import-paths": noRelativeImportPaths,
        },

        languageOptions: {
            parser: tsParser,
            ecmaVersion: "latest",
            sourceType: "module",

            parserOptions: {
                project: true,
                projectService: {
                    allowDefaultProject: ["*.mjs"],
                },
            },
        },

        rules: {
            "react-hooks/exhaustive-deps": "off",

            "no-restricted-syntax": ["error", {
                selector: "Property[key.name='preview'][value.value=true]",
                message: "Make sure to turn 'preview' off before committing.",
            }],

            "no-relative-import-paths/no-relative-import-paths": ["error", {
                rootDir: ".",
                prefix: "@",
            }],
        },
    },
]));
