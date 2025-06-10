import { CodegenConfig } from "@graphql-codegen/cli";
import { HASURA_URL, OSO_API_KEY } from "@/lib/config";
console.log(HASURA_URL);

const SCHEMA: Record<string, any> = {};
SCHEMA[HASURA_URL] = {
  headers: {
    Authorization: `Bearer ${OSO_API_KEY}`,
  },
};
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
