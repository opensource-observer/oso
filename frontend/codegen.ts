import { CodegenConfig } from "@graphql-codegen/cli";
import dotenv from "dotenv";
const envPath = [__dirname, "./.env.local"].join("/");
dotenv.config();
dotenv.config({ path: envPath, override: true });

const DB_GRAPHQL_URL = process.env.NEXT_PUBLIC_DB_GRAPHQL_URL;
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
