import { TEST_ONLY_ALLOW_CLEAR_DB, ENABLE_DB_TESTS } from "../config.js";
import { logger } from "../utils/logger.js";
import { AppDataSource } from "./data-source.js";
import { it, describe, beforeEach, afterAll } from "@jest/globals";
import { randomUUID } from "crypto";

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

type IT_PARAMS = Parameters<typeof it>;
type DESCRIBE_PARAMS = Parameters<typeof describe>;

/**
 * Helper for writing db tests. Should only be used as a top level describe. Use
 * `describe()` for any subsequent levels of describe.
 */
export function withDbDescribe(...args: DESCRIBE_PARAMS) {
  const id = randomUUID();
  if (ENABLE_DB_TESTS) {
    describe(`Database setup for ${args[0]}: ${id}`, () => {
      beforeEach(async () => {
        await clearDb();

        await new Promise((resolve) => {
          setTimeout(() => {
            resolve(null);
          }, 1000);
        });
      });

      afterAll(async () => {
        try {
          await AppDataSource.destroy();
        } catch (_e) {
          console.log("data source already disconnected");
        }
      });

      describe(...args);
    });
  } else {
    describe.skip(...args);
  }
}

export function withDbIt(...args: IT_PARAMS) {
  if (ENABLE_DB_TESTS) {
    return it(...args);
  } else {
    return it.skip(...args);
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
