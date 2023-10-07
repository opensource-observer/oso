import "reflect-metadata";
import path from "path";
import { DataSource, DataSourceOptions, LoggerOptions } from "typeorm";

import {
  DB_DATABASE,
  DB_HOST,
  DB_PASSWORD,
  DB_PORT,
  DB_USER,
  DEBUG_DB,
  NO_DYNAMIC_LOADS,
} from "../config.js";
import {
  Artifact,
  Collection,
  Project,
  Event,
  EventPointer,
  Job,
  JobGroupLock,
  JobExecution,
  Log,
  EventsDailyByArtifact,
  EventsDailyByProject,
} from "./orm-entities.js";

const loggingOption: LoggerOptions = DEBUG_DB ? ["query", "error"] : false;

const dynamicallyLoadedDataSource: DataSourceOptions = {
  type: "postgres",
  host: DB_HOST,
  port: parseInt(DB_PORT),
  username: DB_USER,
  password: DB_PASSWORD,
  database: DB_DATABASE,
  synchronize: true,
  logging: loggingOption,

  entities: [path.resolve("./src/db/orm-entities.ts")],
  migrations: [path.resolve("./src/db/migration/**/*.ts")],
  subscribers: [],
};

/**
 * This is wrapped in a function so we can easily use this for testing.
 *
 * @param databaseName Name of the database to use
 * @returns
 */
export function staticDataSourceOptions(
  databaseName: string,
): DataSourceOptions {
  return {
    type: "postgres",
    host: DB_HOST,
    port: parseInt(DB_PORT),
    username: DB_USER,
    password: DB_PASSWORD,
    database: databaseName,
    synchronize: true,
    logging: loggingOption,

    entities: [
      Artifact,
      Collection,
      Project,
      Event,
      EventPointer,
      Job,
      JobGroupLock,
      JobExecution,
      Log,
      EventsDailyByArtifact,
      EventsDailyByProject,
    ],
    migrations: [],
    subscribers: [],
  };
}

export function testingDataSource(databaseName: string): DataSource {
  return new DataSource(staticDataSourceOptions(databaseName));
}

// Unfortunately, jest seems to error when using this. We cannot use dynamic
// imports. It's possible that this can be fixed in the future but for now this
// is something that is unavoidable. See:
// https://github.com/typeorm/typeorm/issues/10212. This following is a hacky
// solution so that we use dynamic normally and non-dynamic for tests which is
// particularly important for migrations
export const appDataSourceOptions = NO_DYNAMIC_LOADS
  ? staticDataSourceOptions(DB_DATABASE)
  : dynamicallyLoadedDataSource;
export const AppDataSource = new DataSource(appDataSourceOptions);
