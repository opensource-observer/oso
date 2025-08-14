module.exports = {
  env: {
    browser: true,
    es2021: true,
    node: true,
  },
  extends: [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:react/recommended",
    "prettier",
  ],
  ignorePatterns: [
    "**/vendor/*.js",
    "vendor/**/*.js",
    "**/test.only/**",
    "**/utilities/**",
    "**/.eslintrc.js",
    "**/postcss.config.js",
    "!.storybook",
    //"**/next.config.js",
    //"**/tailwind.config.js",
    //"**/.env",
  ],
  parser: "@typescript-eslint/parser",
  parserOptions: {
    ecmaFeatures: {
      jsx: true,
    },
    ecmaVersion: "latest",
    sourceType: "module",
    tsconfigRootDir: __dirname,
    project: "./tsconfig.json",
  },
  plugins: ["unused-imports", "@typescript-eslint", "react"],
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
    "unused-imports/no-unused-vars": [
      "warn",
      {
        vars: "all",
        varsIgnorePattern: "^_",
        args: "after-used",
        argsIgnorePattern: "^_",
      },
    ],
    "no-restricted-properties": [
      "error",
      {
        object: "console",
        property: "error",
        message: "Please use the logger instead.",
      },
    ],
    "no-restricted-globals": [
      "error",
      {
        name: "prompt",
        message: "Please use a React modal instead.",
      },
    ],
  },
};
