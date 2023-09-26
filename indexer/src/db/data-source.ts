import "reflect-metadata";
import path from "path";
import { DataSource } from "typeorm";

import {
  DB_DATABASE,
  DB_HOST,
  DB_PASSWORD,
  DB_PORT,
  DB_USER,
} from "../config.js";
import {
  Artifact,
  Collection,
  Project,
  Event,
  EventPointer,
  Job,
  JobExecution,
  Log,
} from "./orm-entities.js";

export const AppDataSource = new DataSource({
  type: "postgres",
  host: DB_HOST,
  port: parseInt(DB_PORT),
  username: DB_USER,
  password: DB_PASSWORD,
  database: DB_DATABASE,
  synchronize: true,
  logging: false,
  //entities: [path.resolve("./src/db/orm-entities.ts")],

  // Unfortunately, jest seems to error when using this. We cannot use dynamic
  // imports. It's possible that this can be fixed in the future but for now
  // this is something that is unavoidable.
  // See: https://github.com/typeorm/typeorm/issues/10212
  entities: [
    Artifact,
    Collection,
    Project,
    Event,
    EventPointer,
    Job,
    JobExecution,
    Log,
  ],
  migrations: [path.resolve("./src/db/migration/**/*.ts")],
  subscribers: [],
});
