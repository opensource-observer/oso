/* eslint no-restricted-properties: 0 */
import { handleError } from "../utils/error.js";
import { Argv } from "yargs";
import { AppDataSource } from "../db/data-source.js";
import { DateTime } from "luxon";
import { coerceDateTime, coerceDateTimeOrNow } from "../utils/cli.js";
import { logger } from "../utils/logger.js";

export type UtilitiesRefreshAggregatesArgs = {
  startDate: DateTime;
  endDate: DateTime;
  intervalDays: number;
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
}

export async function refreshAggregates(
  args: UtilitiesRefreshAggregatesArgs,
): Promise<void> {
  const aggregatesList = [
    "events_daily_from_artifact",
    "events_daily_to_artifact",
    "events_daily_from_project",
    "events_daily_to_project",
    "events_monthly_from_artifact",
    "events_monthly_to_artifact",
    "events_monthly_from_project",
    "events_monthly_to_project",
    "events_weekly_from_artifact",
    "events_weekly_to_artifact",
    "events_weekly_from_project",
    "events_weekly_to_project",
  ];
  const materialized = ["first_contribution_to_project"];
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
