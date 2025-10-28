import path from "node:path";
import { includeIgnoreFile } from "@eslint/compat";
import rootConfig from "../../eslint.config.mjs";

const gitignorePath = path.resolve(new URL(".", import.meta.url).pathname, ".gitignore");

export default [
    includeIgnoreFile(gitignorePath),
    {
        ignores: [
            "node_modules",
            "src/components/plasmic/generated/",
            "static/plasmic/",
            "build",
            "**/.docusaurus",
            "**/.cache-loader",
            "**/.DS_Store",
            "**/.env.local",
            "**/.env.development.local",
            "**/.env.test.local",
            "**/.env.production.local",
            "**/npm-debug.log*",
            "**/yarn-debug.log*",
            "**/yarn-error.log*",
        ],
    }, ...rootConfig, {
        languageOptions: {
            ecmaVersion: 5,
            sourceType: "script",

            parserOptions: {
                project: ["./tsconfig.json"],
            },
        },

        rules: {
            "@typescript-eslint/ban-ts-comment": "off",
            "@typescript-eslint/no-empty-object-type": "off",
        },
    }
];