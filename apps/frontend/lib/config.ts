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
export const POSTHOG_KEY =
  process.env.NEXT_PUBLIC_POSTHOG_KEY ?? "MISSING POSTHOG_KEY";
export const GOOGLE_ANALYTICS_KEY =
  process.env.NEXT_PUBLIC_GOOGLE_ANALYTICS_KEY ??
  "MISSING GOOGLE_ANALYTICS_KEY";
export const PLASMIC_PROJECT_ID =
  process.env.PLASMIC_PROJECT_ID ?? "MISSING PLASMIC_PROJECT_ID";
export const PLASMIC_PROJECT_API_TOKEN =
  process.env.PLASMIC_PROJECT_API_TOKEN ?? "MISSING PLASMIC_PROJECT_API_TOKEN";
export const DOMAIN = requireEnv(
  process.env.NEXT_PUBLIC_DOMAIN,
  "NEXT_PUBLIC_DOMAIN",
);
export const DB_GRAPHQL_URL = requireEnv(
  process.env.NEXT_PUBLIC_DB_GRAPHQL_URL,
  "NEXT_PUBLIC_DB_GRAPHQL_URL",
);
export const HASURA_URL = process.env.HASURA_URL ?? "MISSING HASURA_URL";
export const HASURA_PAT = process.env.HASURA_PAT ?? "MISSING HASURA_PAT";
export const OSO_API_KEY = process.env.OSO_API_KEY ?? "MISSING OSO_API_KEY";

export const SUPABASE_URL = requireEnv(
  process.env.NEXT_PUBLIC_SUPABASE_URL,
  "NEXT_PUBLIC_SUPABASE_URL",
);
export const SUPABASE_ANON_KEY = requireEnv(
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
  "NEXT_PUBLIC_SUPABASE_ANON_KEY",
);
export const SUPABASE_SERVICE_KEY =
  process.env.SUPABASE_SERVICE_KEY ?? "MISSING SUPABASE_SERVICE_KEY";
export const SUPABASE_JWT_SECRET =
  process.env.SUPABASE_JWT_SECRET ?? "MISSING SUPABASE_JWT_SECRET";
export const CLICKHOUSE_URL =
  process.env.CLICKHOUSE_URL ?? "MISSING CLICKHOUSE_URL";
export const CLICKHOUSE_USERNAME =
  process.env.CLICKHOUSE_USERNAME ?? "MISSING CLICKHOUSE_USERNAME";
export const CLICKHOUSE_PASSWORD =
  process.env.CLICKHOUSE_PASSWORD ?? "MISSING CLICKHOUSE_PASSWORD";
export const CLICKHOUSE_DB_NAME = process.env.CLICKHOUSE_DB_NAME ?? "default";

export const TRINO_URL = process.env.TRINO_URL ?? "MISSING TRINO_URL";
export const TRINO_ADMIN_USER =
  process.env.TRINO_ADMIN_USER ?? "MISSING TRINO_USERNAME";
export const TRINO_ADMIN_PASSWORD =
  process.env.TRINO_ADMIN_PASSWORD ?? "MISSING TRINO_PASSWORD";
export const TRINO_CATALOG = process.env.TRINO_CATALOG ?? "iceberg";
export const TRINO_SCHEMA = process.env.TRINO_SCHEMA ?? "oso";

export const ALGOLIA_APPLICATION_ID =
  process.env.NEXT_PUBLIC_ALGOLIA_APPLICATION_ID ??
  "MISSING ALGOLIA_APPLICATION_ID";
export const ALGOLIA_API_KEY =
  process.env.NEXT_PUBLIC_ALGOLIA_API_KEY ?? "MISSING ALGOLIA_API_KEY";
export const ALGOLIA_INDEX =
  process.env.NEXT_PUBLIC_ALGOLIA_INDEX ?? "MISSING ALGOLIA_INDEX";
export const FEEDBACK_FARM_ID =
  process.env.NEXT_PUBLIC_FEEDBACK_FARM_ID ?? "MISSING FEEDBACK_FARM_ID";
export const OSO_AGENT_URL =
  process.env.OSO_AGENT_URL ?? "MISSING OSO_AGENT_URL";
export const STRIPE_SECRET_KEY =
  process.env.STRIPE_SECRET_KEY ?? "MISSING STRIPE_SECRET_KEY";
export const STRIPE_PUBLISHABLE_KEY =
  process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY ??
  "MISSING STRIPE_PUBLISHABLE_KEY";
export const STRIPE_WEBHOOK_SECRET =
  process.env.STRIPE_WEBHOOK_SECRET ?? "MISSING STRIPE_WEBHOOK_SECRET";
export const OSO_ENTITIES_KEY = "oso_entities";
export const OSO_ENTITIES = [
  "artifact.artifact_id",
  "project.project_id",
  "metrics.metric_id",
];
