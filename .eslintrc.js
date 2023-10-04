module.exports = {
  "env": {
    "browser": true,
    "es2021": true,
    "node": true
  },
  "extends": [
    "eslint:recommended",
    "plugin:react/recommended",
    "plugin:@typescript-eslint/recommended",
    "prettier",
    "next/core-web-vitals"
  ],
  "ignorePatterns": [
    "**/vendor/*.js",
    "vendor/**/*.js",
    "**/jest.config.ts",
    "**/test.only/**",
    "**/utilities/**",
    "**/next.config.js",
    "**/postcss.config.js",
    "**/tailwind.config.js",
    "**/.env"
  ],
  "parser": "@typescript-eslint/parser",
  "parserOptions": {
    "ecmaFeatures": {
      "jsx": true
    },
    "ecmaVersion": "latest",
    "sourceType": "module",
    "project": "tsconfig.json",
    "tsconfigRootDir": __dirname,
  },
  "plugins": [
    "react",
    "@typescript-eslint"
  ],
  "rules": {
    "react-hooks/exhaustive-deps": "off",
    "@typescript-eslint/no-misused-promises": "error",
    "@typescript-eslint/no-floating-promises": "error",
    "@typescript-eslint/no-explicit-any": "off",
    "@typescript-eslint/no-unused-vars": [
      "warn",
      {
        "argsIgnorePattern": "^_"
      }
    ],
    "no-restricted-properties": [
      "error",
      {
        "object": "console",
        "property": "error",
        "message": "Please use the logger instead."
      }
    ],
    "no-restricted-globals": [
      "error",
      {
        "name": "prompt",
        "message": "Please use a React modal instead."
      }
    ],
    "no-restricted-syntax": [
      "error",
      {
        "selector": "Property[key.name='preview'][value.value=true]",
        "message": "Make sure to turn 'preview' off before committing."
      }
    ]
  }
}