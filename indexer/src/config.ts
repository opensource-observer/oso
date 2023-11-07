import * as dotenv from "dotenv";
dotenv.config();

export const requireEnv = (identifier: string) => {
  const value = process.env[identifier];

  if (!value) {
    throw new Error(`Required env var ${identifier} does not exist`);
  }
  return value;
};

export const DB_HOST = requireEnv("DB_HOST");
export const DB_PORT = requireEnv("DB_PORT");
export const DB_USER = requireEnv("DB_USER");
export const DB_PASSWORD = requireEnv("DB_PASSWORD");
export const DB_DATABASE = requireEnv("DB_DATABASE");
export const GITHUB_GRAPHQL_API = requireEnv("X_GITHUB_GRAPHQL_API");
export const GITHUB_TOKEN = requireEnv("X_GITHUB_TOKEN");
export const DUNE_API_KEY = requireEnv("DUNE_API_KEY");
export const DUNE_CONTRACTS_TABLES_DIR =
  process.env.DUNE_CONTRACTS_TABLES_DIR || "";
export const TEST_ONLY_ALLOW_CLEAR_DB =
  process.env.TEST_ONLY_ALLOW_CLEAR_DB === "true" || false;
export const NO_DYNAMIC_LOADS =
  process.env.NO_DYNAMIC_LOADS === "true" || false;
export const GITHUB_WORKERS_OWNER = process.env.GITHUB_WORKERS_OWNER
  ? process.env.GITHUB_WORKERS_OWNER
  : "opensource-observer";
export const GITHUB_WORKERS_REPO = process.env.GITHUB_WORKERS_REPO
  ? process.env.GITHUB_WORKERS_REPO
  : "oso";
export const GITHUB_WORKERS_REF = process.env.GITHUB_WORKERS_REF
  ? process.env.GITHUB_WORKERS_REF
  : "main";
export const GITHUB_WORKERS_WORKFLOW_ID = process.env.GITHUB_WORKERS_WORKFLOW_ID
  ? process.env.GITHUB_WORKERS_WORKFLOW_ID
  : "indexer-worker.yml";
export const ENABLE_DB_TESTS = process.env.ENABLE_DB_TESTS === "true" || false;
export const INDEXER_SPAWN = process.env.INDEXER_SPAWN === "true" || false;
export const DEBUG_DB = process.env.DEBUG_DB === "true" || false;
export const DB_APPLICATION_NAME =
  process.env.DB_APPLICATION_NAME !== ""
    ? process.env.DB_APPLICATION_NAME
    : "indexer-default";

// This should never be set to true for production. This might cause data loss.
export const DB_SYNCHRONIZE = process.env.DB_SYNCHRONIZE === "true" || false;
