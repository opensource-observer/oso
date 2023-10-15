import dotenv from "dotenv";

const envPath = [__dirname, "../.env.local"].join("/");
dotenv.config();
dotenv.config({ path: envPath, override: true });

export const requireEnv = (value: string | undefined, identifier: string) => {
  if (!value) {
    throw new Error(`Required env var ${identifier} does not exist`);
  }
  return value;
};

export const PLASMIC_PROJECT_ID = process.env.PLASMIC_PROJECT_ID ?? "MISSING";
export const PLASMIC_PROJECT_API_TOKEN =
  process.env.PLASMIC_PROJECT_API_TOKEN ?? "MISSING";

export const DOMAIN = requireEnv(
  process.env.NEXT_PUBLIC_DOMAIN,
  "NEXT_PUBLIC_DOMAIN",
);

export const DB_GRAPHQL_URL = requireEnv(
  process.env.NEXT_PUBLIC_DB_GRAPHQL_URL,
  "NEXT_PUBLIC_DB_GRAPHQL_URL",
);

export const SUPABASE_URL = requireEnv(
  process.env.NEXT_PUBLIC_SUPABASE_URL,
  "NEXT_PUBLIC_SUPABASE_URL",
);

export const SUPABASE_ANON_KEY = requireEnv(
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
  "NEXT_PUBLIC_SUPABASE_ANON_KEY",
);

export const ALGOLIA_APPLICATION_ID = requireEnv(
  process.env.NEXT_PUBLIC_ALGOLIA_APPLICATION_ID,
  "NEXT_PUBLIC_ALGOLIA_APPLICATION_ID",
);

export const ALGOLIA_API_KEY = requireEnv(
  process.env.NEXT_PUBLIC_ALGOLIA_API_KEY,
  "NEXT_PUBLIC_ALGOLIA_API_KEY",
);

export const ALGOLIA_INDEX = requireEnv(
  process.env.NEXT_PUBLIC_ALGOLIA_INDEX,
  "NEXT_PUBLIC_ALGOLIA_INDEX",
);

export const FEEDBACK_FARM_ID = requireEnv(
  process.env.NEXT_PUBLIC_FEEDBACK_FARM_ID,
  "NEXT_PUBLIC_FEEDBACK_FARM_ID",
);
