import { CodegenConfig } from "@graphql-codegen/cli";
import { DAGSTER_GRAPHQL_URL, HASURA_URL, OSO_API_KEY } from "@/lib/config";

const SCHEMA: Record<string, any> = {};
SCHEMA[HASURA_URL] = {
  headers: {
    Authorization: `Bearer ${OSO_API_KEY}`,
  },
};
SCHEMA[DAGSTER_GRAPHQL_URL] = {};
const config: CodegenConfig = {
  schema: SCHEMA,
  documents: [
    "app/**/*.{ts,tsx}",
    "pages/**/*.{ts,tsx}",
    "components/**/*.{ts,tsx}",
    "lib/**/*.{ts,tsx}",
  ],
  generates: {
    "./lib/graphql/generated/": {
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
