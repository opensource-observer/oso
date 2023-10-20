import { TEST_ONLY_ALLOW_CLEAR_DB, ENABLE_DB_TESTS } from "../config.js";
import { logger } from "../utils/logger.js";
import { AppDataSource } from "./data-source.js";
import { it, describe, beforeEach, afterAll } from "@jest/globals";
import { randomUUID } from "crypto";
import { EventTypeEnum } from "./orm-entities.js";

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
    const repository = AppDataSource.getRepository(entity.name);
    await repository.query(
      `TRUNCATE ${entity.tableName} RESTART IDENTITY CASCADE`,
    );
  }
  // Initialize the event type table. It's fairly critical and the application
  // tends to treat it as static.
  const enumValues = Object.keys(EventTypeEnum);
  const keys = Object.values(enumValues);

  // Initialize the event type table. Not worrying about sql injection
  // here. We're the ones providing input.
  await c.createQueryRunner().query(
    `
      insert into event_type(name, version)
      select unnest($1::text[]), 1
    `,
    [keys],
  );
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
        try {
          await clearDb();
        } catch (err) {
          // eslint-disable-next-line no-restricted-properties
          console.error(err);
          throw err;
        }
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

export async function initializeOnce() {
  if (AppDataSource.isInitialized) {
    await AppDataSource.destroy();
  }
  return await AppDataSource.initialize();
}
