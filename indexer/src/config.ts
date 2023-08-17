import * as dotenv from "dotenv";
dotenv.config();

export const requireEnv = (identifier: string) => {
  const value = process.env[identifier];

  if (!value) {
    throw new Error(`Required env var ${identifier} does not exist`);
  }
  return value;
};

export const DATABASE_URL = requireEnv("DATABASE_URL");
export const GITHUB_GRAPHQL_API = requireEnv("X_GITHUB_GRAPHQL_API");
export const GITHUB_TOKEN = requireEnv("X_GITHUB_TOKEN");
export const DUNE_API_KEY = requireEnv("DUNE_API_KEY");
