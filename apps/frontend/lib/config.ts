/**
 * Mark an environment as required for the build.
 * This is mostly used for convenience of debugging, so that things break early
 * Note: this should only be used for environment variables prefixed with "NEXT_PUBLIC_".
 *  Client-side bundles will be missing other env variables by definition
 */
export const requireEnv = (value: string | undefined, identifier: string) => {
  if (!value) {
    throw new Error(`Required env var ${identifier} does not exist`);
  }
  return value;
};

export const NODE_ENV = process.env.NODE_ENV ?? "development";
export const STATIC_EXPORT = !!process.env.STATIC_EXPORT;
export const POSTHOG_HOST = "/ingest";
export const POSTHOG_HOST_DIRECT = "https://us.i.posthog.com";
export const POSTHOG_KEY = process.env.NEXT_PUBLIC_POSTHOG_KEY ?? "MISSING";
export const GOOGLE_ANALYTICS_KEY =
  process.env.NEXT_PUBLIC_GOOGLE_ANALYTICS_KEY ?? "MISSING";
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
export const HASURA_URL = process.env.HASURA_URL ?? "MISSING";
export const HASURA_PAT = process.env.HASURA_PAT;
export const OSO_API_KEY = process.env.OSO_API_KEY;

export const SUPABASE_URL = requireEnv(
  process.env.NEXT_PUBLIC_SUPABASE_URL,
  "NEXT_PUBLIC_SUPABASE_URL",
);
export const SUPABASE_ANON_KEY = requireEnv(
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
  "NEXT_PUBLIC_SUPABASE_ANON_KEY",
);
export const SUPABASE_SERVICE_KEY =
  process.env.SUPABASE_SERVICE_KEY ?? "MISSING";
export const SUPABASE_JWT_SECRET = process.env.SUPABASE_JWT_SECRET ?? "MISSING";
export const CLICKHOUSE_URL = process.env.CLICKHOUSE_URL ?? "MISSING";
export const CLICKHOUSE_USERNAME = process.env.CLICKHOUSE_USERNAME ?? "MISSING";
export const CLICKHOUSE_PASSWORD = process.env.CLICKHOUSE_PASSWORD ?? "MISSING";
export const CLICKHOUSE_DB_NAME = process.env.CLICKHOUSE_DB_NAME ?? "default";

export const TRINO_URL = process.env.TRINO_URL ?? "MISSING";
export const TRINO_USERNAME = process.env.TRINO_USERNAME ?? "MISSING";
export const TRINO_PASSWORD = process.env.TRINO_PASSWORD ?? "MISSING";
export const TRINO_CATALOG = process.env.TRINO_CATALOG ?? "iceberg";
export const TRINO_SCHEMA = process.env.TRINO_SCHEMA ?? "oso";

export const ALGOLIA_APPLICATION_ID =
  process.env.NEXT_PUBLIC_ALGOLIA_APPLICATION_ID ?? "MISSING";
export const ALGOLIA_API_KEY =
  process.env.NEXT_PUBLIC_ALGOLIA_API_KEY ?? "MISSING";
export const ALGOLIA_INDEX = process.env.NEXT_PUBLIC_ALGOLIA_INDEX ?? "MISSING";
export const FEEDBACK_FARM_ID =
  process.env.NEXT_PUBLIC_FEEDBACK_FARM_ID ?? "MISSING";
export const GOOGLE_AI_API_KEY = process.env.GOOGLE_AI_API_KEY ?? "MISSING";
