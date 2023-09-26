import { TEST_ONLY_ALLOW_CLEAR_DB } from "../config.js";
import { logger } from "../utils/logger.js";
import { AppDataSource } from "./data-source.js";

// Testing utilities for the database
export async function clearDb() {
  if (!TEST_ONLY_ALLOW_CLEAR_DB) {
    logger.warn(
      "a code path attempted to clear the database when it is intended only for testing",
    );
    throw new Error("clearing the database is not allowed");
  }
  const c = await initializeOnce();
  const entities = c.entityMetadatas;
  for (const entity of entities) {
    const repository = await AppDataSource.getRepository(entity.name);
    await repository.query(
      `TRUNCATE ${entity.tableName} RESTART IDENTITY CASCADE`,
    );
  }
}

export let isDbInitialized = false;

export async function initializeOnce() {
  if (!isDbInitialized) {
    isDbInitialized = true;
    return await AppDataSource.initialize();
  }
  return AppDataSource;
}
