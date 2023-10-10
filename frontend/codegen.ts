import { CodegenConfig } from "@graphql-codegen/cli";
import { DB_GRAPHQL_URL } from "./lib/config";
console.log(DB_GRAPHQL_URL);

const config: CodegenConfig = {
  schema: DB_GRAPHQL_URL,
  documents: [
    "app/**/*.{ts,tsx}",
    "pages/**/*.{ts,tsx}",
    "components/**/*.{ts,tsx}",
    "lib/**/*.{ts,tsx}",
  ],
  generates: {
    "./lib/__generated__/": {
      preset: "client",
      plugins: [],
      presetConfig: {
        gqlTagName: "gql",
      },
    },
  },
  ignoreNoDocuments: true,
};

export default config;
