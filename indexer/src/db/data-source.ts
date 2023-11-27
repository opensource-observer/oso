import "reflect-metadata";
import path from "path";
import { fileURLToPath } from "url";
import { DataSource, DataSourceOptions, LoggerOptions } from "typeorm";
import _ from "lodash";

import {
  DB_DATABASE,
  DB_HOST,
  DB_PASSWORD,
  DB_PORT,
  DB_USER,
  DEBUG_DB,
  NO_DYNAMIC_LOADS,
  DB_APPLICATION_NAME,
  DB_SYNCHRONIZE,
} from "../config.js";
import {
  Artifact,
  CollectionType,
  Collection,
  Project,
  Event,
  EventPointer,
  EventType,
  Recording,
  RecorderTempDuplicateEvent,
  RecorderTempEvent,
  RecorderTempEventArtifact,
  Job,
  JobGroupLock,
  JobExecution,
  Log,
  FirstContributionToProject,
  LastContributionToProject,
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
  EventsDailyToCollection,
  EventsWeeklyToCollection,
  EventsMonthlyToCollection,
} from "./orm-entities.js";

const loggingOption: LoggerOptions = DEBUG_DB ? "all" : false;
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export interface OSODataSourceOptions {
  connectionSuffix: string;
}

const defaultOSODataSourceOptions: OSODataSourceOptions = {
  connectionSuffix: "",
};

export function dynamicallyLoadedDataSource(
  options?: Partial<OSODataSourceOptions>,
): DataSourceOptions {
  const opts = _.merge(defaultOSODataSourceOptions, options);
  return {
    type: "postgres",
    host: DB_HOST,
    port: parseInt(DB_PORT),
    username: DB_USER,
    password: DB_PASSWORD,
    database: DB_DATABASE,
    synchronize: DB_SYNCHRONIZE,
    logging: loggingOption,
    applicationName: `${DB_APPLICATION_NAME}${opts.connectionSuffix}`,

    entities: [path.resolve(__dirname, "./orm-entities.ts")],
    migrations: [path.resolve(__dirname, "./migration/**/*.ts")],
    subscribers: [],
  };
}

/**
 * This is wrapped in a function so we can easily use this for testing.
 *
 * @param databaseName Name of the database to use
 * @returns
 */
export function staticDataSourceOptions(
  databaseName: string,
  options?: Partial<OSODataSourceOptions>,
): DataSourceOptions {
  const opts = _.merge(defaultOSODataSourceOptions, options);
  return {
    type: "postgres",
    host: DB_HOST,
    port: parseInt(DB_PORT),
    username: DB_USER,
    password: DB_PASSWORD,
    database: databaseName,
    synchronize: DB_SYNCHRONIZE,
    logging: loggingOption,
    applicationName: `${DB_APPLICATION_NAME}${opts.connectionSuffix}`,

    entities: [
      Artifact,
      CollectionType,
      Collection,
      Project,
      Event,
      EventPointer,
      Recording,
      RecorderTempDuplicateEvent,
      RecorderTempEvent,
      RecorderTempEventArtifact,
      Job,
      JobGroupLock,
      JobExecution,
      Log,
      FirstContributionToProject,
      LastContributionToProject,
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
      EventsDailyToCollection,
      EventsWeeklyToCollection,
      EventsMonthlyToCollection,
      EventType,
    ],
    migrations: [],
    subscribers: [],
  };
}

function testingDataSource(databaseName: string): DataSource {
  return new DataSource(staticDataSourceOptions(databaseName));
}

/**
 * Creates a new app data source and connection
 * @param id string used to name the connection
 */
export function createNewAppDataSource(id: string): DataSource {
  // Unfortunately, jest seems to error when using this. We cannot use dynamic
  // imports. It's possible that this can be fixed in the future but for now this
  // is something that is unavoidable. See:
  // https://github.com/typeorm/typeorm/issues/10212. This following is a hacky
  // solution so that we use dynamic normally and non-dynamic for tests which is
  // particularly important for migrations
  return new DataSource(
    NO_DYNAMIC_LOADS
      ? staticDataSourceOptions(DB_DATABASE, { connectionSuffix: `-${id}` })
      : dynamicallyLoadedDataSource({ connectionSuffix: `-${id}` }),
  );
}

export async function createAndConnectDataSource(
  id: string,
): Promise<DataSource> {
  const ds = createNewAppDataSource(id);
  await ds.initialize();
  return ds;
}

export const AppDataSource = createNewAppDataSource("default");

async function initializeDataSource() {
  if (!AppDataSource.isInitialized) {
    await AppDataSource.initialize();
  }
}

export { initializeDataSource, testingDataSource };
