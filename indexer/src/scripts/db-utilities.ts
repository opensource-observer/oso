/* eslint no-restricted-properties: 0 */
import { handleError } from "../utils/error.js";
import { Argv } from "yargs";
import { AppDataSource } from "../db/data-source.js";
import { DateTime } from "luxon";
import { coerceDateTime, coerceDateTimeOrNow } from "../utils/cli.js";
import { logger } from "../utils/logger.js";
import { Recording } from "../db/orm-entities.js";
import { LessThan } from "typeorm";
import _ from "lodash";

export type UtilitiesRefreshAggregatesArgs = {
  startDate: DateTime;
  endDate: DateTime;
  intervalDays: number;
};

export type CleanRecorderTempTableArgs = {
  olderThanDate: DateTime | null;
};

export function dbUtilitiesCommandGroup(topYargs: Argv) {
  topYargs.command<UtilitiesRefreshAggregatesArgs>(
    "refresh-mvs",
    "Refreshes materialized views",
    (yargs) => {
      yargs
        .option("start-date", {
          type: "string",
          describe: "ISO8601 of the start date",
          default: "2015-01-01T00:00:00Z",
        })
        .coerce("start-date", coerceDateTime)
        .option("end-date", {
          type: "string",
          describe: "ISO8601 of the end date (defaults to now)",
          default: "",
        })
        .coerce("end-date", coerceDateTimeOrNow)
        .option("interval-days", {
          type: "number",
          describe: "interval",
          default: 5000,
        });
    },
    (args) => handleError(refreshAggregates(args)),
  );
  topYargs.command<CleanRecorderTempTableArgs>(
    "clean-recorder-temps",
    "Cleans the recorder temporary tables",
    (yargs) => {
      yargs
        .option("older-than-date", {
          type: "string",
          describe:
            "ISO8601 of the expiration date to use. defaults to using the stored expiration",
          default: "",
        })
        .coerce("older-than-date", coerceDateTimeOrNow);
    },
    (args) => handleError(cleanRecorderTemps(args)),
  );
}

export async function cleanRecorderTemps(args: CleanRecorderTempTableArgs) {
  const repo = AppDataSource.getRepository(Recording);
  const olderThan = args.olderThanDate ? args.olderThanDate : DateTime.now();
  const recordings = await repo.find({
    where: {
      expiration: LessThan(olderThan.toJSDate()),
    },
  });
  for (const recording of recordings) {
    console.log(`Cleaning Recording[${recording.recorderId}]`);
    // Find all tables with the recorderId
    const recorderId = recording.recorderId;
    const recorderIdTableStr = recorderId.replace(/-/g, "_");
    const tablesToDelete = (await AppDataSource.query(
      `
      SELECT tablename FROM pg_catalog.pg_tables where schemaname = 'public' AND tablename LIKE $1;
    `,
      [`%${recorderIdTableStr}%`],
    )) as { tablename: string }[];
    if (tablesToDelete.length > 0) {
      logger.debug(`deleting tables for Recording[${recorderId}]`);
      await AppDataSource.query(`
        DROP TABLE ${tablesToDelete.map((a) => a.tablename).join(", ")}
      `);
    }
    logger.debug(`deleting Recording[${recorderId}]`);
    await repo.delete(recorderId);
  }
}

export async function refreshAggregates(
  args: UtilitiesRefreshAggregatesArgs,
): Promise<void> {
  // Query for all of the continous aggregate names. These will be excluded from
  // the materialized views list
  const rawAggregates = (await AppDataSource.query(`
    SELECT view_name 
    FROM timescaledb_information.continuous_aggregates
    WHERE view_schema = 'public'
  `)) as { view_name: string }[];

  const aggregatesList = _.uniq(rawAggregates.map((a) => a.view_name));

  const entities = AppDataSource.entityMetadatas;
  const materialized: string[] = [];
  for (const entity of entities) {
    if (entity.tableMetadataArgs.type !== "view") {
      continue;
    }
    const name = entity.tableName;
    // Don't include views from the continous aggregates. Those are refreshed
    // differently
    if (
      entity.tableMetadataArgs.materialized &&
      aggregatesList.indexOf(name) === -1
    ) {
      materialized.push(entity.tableName);
    }
  }

  console.log("Found the following materialized views %j", materialized);
  console.log("Found the following continous aggregates %j", aggregatesList);

  const startDate = args.startDate;
  const endDate = args.endDate!;
  const intervalDays = args.intervalDays;

  for (const mv of materialized) {
    logger.info(`Refreshing ${mv}`);
    const resp = await AppDataSource.query(`
      REFRESH MATERIALIZED VIEW ${mv} 
    `);
    logger.info("Refresh response");
    logger.info(resp);
  }

  // Continuous aggregates will start
  for (const agg of aggregatesList) {
    let currentStart = endDate.minus({ days: intervalDays });
    let currentEnd = endDate;
    while (currentEnd >= startDate) {
      logger.info(
        `Refreshing ${agg} for ${currentStart.toISODate()} to ${currentEnd.toISODate()}`,
      );
      const resp = await AppDataSource.query(
        `
          CALL refresh_continuous_aggregate($1, $2::timestamptz, $3::timestamptz)
        `,
        [agg, startDate, endDate],
      );
      currentStart = currentStart.minus({ days: intervalDays });
      currentEnd = currentEnd.minus({ days: intervalDays });
      if (currentStart < startDate) {
        currentStart = startDate;
      }
      logger.info("Refresh response");
      logger.info(resp);
    }
  }
}
