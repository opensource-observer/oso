import "reflect-metadata";
import path from "path";
import { fileURLToPath } from "url";
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
  EventType,
  Job,
  JobGroupLock,
  JobExecution,
  Log,
  FirstContribution,
  EventsDailyToArtifact,
  EventsWeeklyToArtifact,
  EventsMonthlyToArtifact,
  EventsDailyToProject,
  EventsWeeklyToProject,
  EventsMonthlyToProject,
  EventsDailyFromArtifact,
  EventsWeeklyFromArtifact,
  EventsMonthlyFromArtifact,
  EventsDailyFromProject,
  EventsWeeklyFromProject,
  EventsMonthlyFromProject,
} from "./orm-entities.js";

const loggingOption: LoggerOptions = DEBUG_DB ? "all" : false;
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const dynamicallyLoadedDataSource: DataSourceOptions = {
  type: "postgres",
  host: DB_HOST,
  port: parseInt(DB_PORT),
  username: DB_USER,
  password: DB_PASSWORD,
  database: DB_DATABASE,
  synchronize: true,
  logging: loggingOption,

  entities: [path.resolve(__dirname, "./orm-entities.ts")],
  migrations: [path.resolve(__dirname, "./migration/**/*.ts")],
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
      FirstContribution,
      EventsDailyToArtifact,
      EventsWeeklyToArtifact,
      EventsMonthlyToArtifact,
      EventsDailyFromArtifact,
      EventsWeeklyFromArtifact,
      EventsMonthlyFromArtifact,
      EventsDailyToProject,
      EventsWeeklyToProject,
      EventsMonthlyToProject,
      EventsDailyFromProject,
      EventsWeeklyFromProject,
      EventsMonthlyFromProject,
      EventType,
    ],
    migrations: [],
    subscribers: [],
  };
}

function testingDataSource(databaseName: string): DataSource {
  return new DataSource(staticDataSourceOptions(databaseName));
}

// Unfortunately, jest seems to error when using this. We cannot use dynamic
// imports. It's possible that this can be fixed in the future but for now this
// is something that is unavoidable. See:
// https://github.com/typeorm/typeorm/issues/10212. This following is a hacky
// solution so that we use dynamic normally and non-dynamic for tests which is
// particularly important for migrations
const appDataSourceOptions = NO_DYNAMIC_LOADS
  ? staticDataSourceOptions(DB_DATABASE)
  : dynamicallyLoadedDataSource;
const AppDataSource = new DataSource(appDataSourceOptions);

async function initializeDataSource() {
  if (!AppDataSource.isInitialized) {
    await AppDataSource.initialize();
  }
}

export {
  appDataSourceOptions,
  AppDataSource,
  initializeDataSource,
  testingDataSource,
};
