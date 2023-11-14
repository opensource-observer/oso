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
          default: "2005-01-01T00:00:00Z",
        })
        .coerce("start-date", coerceDateTime)
        .option("end-date", {
          type: "string",
          describe: "ISO8601 of the end date (defaults to now)",
          default: "",
        })
        .coerce("end-date", coerceDateTimeOrNow);
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
  const startDate = args.startDate.toISODate()!;
  const endDate = args.endDate.toISODate()!;

  for (const mv of materialized) {
    logger.info(`Refreshing ${mv}`);
    const resp = await AppDataSource.query(`
      REFRESH MATERIALIZED VIEW ${mv} 
    `);
    logger.info("Refresh response");
    logger.info(resp);
  }

  for (const agg of aggregatesList) {
    logger.info(`Refreshing ${agg} for ${startDate} to ${endDate}`);
    const resp = await AppDataSource.query(
      `
      CALL refresh_continuous_aggregate($1, $2::timestamptz, $3::timestamptz)
    `,
      [agg, startDate, endDate],
    );
    logger.info("Refresh response");
    logger.info(resp);
  }
}
