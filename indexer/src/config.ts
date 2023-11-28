import * as dotenv from "dotenv";
dotenv.config();

export function requireEnv(identifier: string) {
  const value = process.env[identifier];

  if (!value) {
    throw new Error(`Required env var ${identifier} does not exist`);
  }
  return value;
}

export function envWithDefault(identifier: string, defaultValue: any) {
  const value = process.env[identifier];
  if (!value) {
    return defaultValue;
  }
  return value;
}

export function envBoolean(
  identifier: string,
  defaultValue: boolean = false,
): boolean {
  if (defaultValue) {
    return process.env[identifier] === "false" ? false : true;
  }
  return process.env[identifier] === "true" ? true : false;
}

export const DB_HOST = requireEnv("DB_HOST");
export const DB_PORT = requireEnv("DB_PORT");
export const DB_USER = requireEnv("DB_USER");
export const DB_PASSWORD = requireEnv("DB_PASSWORD");
export const DB_DATABASE = requireEnv("DB_DATABASE");
export const GITHUB_GRAPHQL_API = requireEnv("X_GITHUB_GRAPHQL_API");
export const GITHUB_TOKEN = requireEnv("X_GITHUB_TOKEN");
export const DUNE_API_KEY = requireEnv("DUNE_API_KEY");
export const DUNE_CSV_DIR_PATH = process.env.DUNE_CSVS_DIR_PATH || "";
export const TEST_ONLY_ALLOW_CLEAR_DB = envBoolean("TEST_ONLY_ALLOW_CLEAR_DB");
export const NO_DYNAMIC_LOADS = envBoolean("NO_DYNAMIC_LOADS");
export const GITHUB_WORKERS_OWNER = envWithDefault(
  "GITHUB_WORKERS_OWNER",
  "opensource-observer",
);
export const GITHUB_WORKERS_REPO = envWithDefault("GITHUB_WORKERS_REPO", "oso");
export const GITHUB_WORKERS_REF = envWithDefault("GITHUB_WORKERS_REF", "main");
export const GITHUB_WORKERS_WORKFLOW_ID = envWithDefault(
  "GITHUB_WORKERS_WORKFLOW_ID",
  "indexer-worker.yml",
);
export const ENABLE_DB_TESTS = envBoolean("ENABLE_DB_TESTS");
export const REDIS_URL = envWithDefault("REDIS_URL", "redis://localhost:6379");
export const INDEXER_SPAWN = envBoolean("INDEXER_SPAWN");
export const DEBUG_DB = envBoolean("DEBUG_DB");
export const DB_APPLICATION_NAME = envWithDefault(
  "DB_APPLICATION_NAME",
  "indexer-default",
);

// This should never be set to true for production. This might cause data loss.
export const DB_SYNCHRONIZE = envBoolean("DB_SYNCHRONIZE");
