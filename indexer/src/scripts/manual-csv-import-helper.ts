// Currently just a test file but if it gets committed that wasn't intentional
// but is also just fine
import { parse } from "csv";
import fs from "fs";
import { DateTime } from "luxon";
import { TimeSeriesLookupNormalizingUnit } from "../cacher/time-series.js";
import { handleError } from "../utils/error.js";
import { Argv } from "yargs";
import _ from "lodash";

export type ImportCsvCommonArgs = {
  dateIndex: number;
  path: string[];
  normalizingUnit: TimeSeriesLookupNormalizingUnit;
  direction: "asc" | "dsc";
};

export function csvCommandGroup(topYargs: Argv) {
  topYargs.command<ImportCsvCommonArgs>(
    "download-assistant",
    "Download assistant that tells you what to query for the next query",
    (yargs) => {
      yargs
        .option("date-index", { default: 0, type: "number" })
        .option("path", { type: "array" })
        .option("normalizing-unit", {
          type: "string",
          choices: ["hour", "day", "month"],
          default: "day",
        });
    },
    (args) => handleError(csvDownloadAssistant(args)),
  );
}

/**
 * Used to backfill data from any csv. Tells you where to query next (if that's
 * needed). Also tells you how many rows you're getting. It checks if the dates
 * are ordered. If they're not this will error. The data must be ordered and a
 * `time` field must be the first field. It will normalize on days by default
 * (this means the date it will give for you to continue from will be normalized
 * to the day/hour/month _before or on_ the second to last available date). This
 * command can be fed multiple paths and it will ensure that these csv files
 * maintain a continous set of results.
 */
export async function csvDownloadAssistant(
  args: ImportCsvCommonArgs,
): Promise<void> {
  let lastScanResult: ScanResult | undefined = undefined;

  if (args.path.length === 0) {
    throw new Error("no input");
  }

  let fullyContinuous = true;

  for (const path of args.path) {
    const scanResult = await csvDownloadScan(
      path,
      args.dateIndex,
      args.normalizingUnit,
      lastScanResult,
    );
    if (!scanResult.isContinuous) {
      if (!lastScanResult) {
        throw new Error("unexpectedly non-continuous from the first csv");
      }
      console.log(
        `Rows between ${scanResult.path} and ${
          lastScanResult!.path
        } are not continuous`,
      );
      fullyContinuous = false;
    }
    lastScanResult = scanResult;
  }

  if (!lastScanResult) {
    throw new Error("there should be a scan result or an error");
  }
  console.log("Scan Result:");
  console.log(`    Final checked path: ${lastScanResult.path}`);
  console.log(`    Are files continuous?: ${fullyContinuous ? "yes" : "no"}`);
  console.log(
    `    Next point date to query: ${lastScanResult.lastPeriodDateTime
      .toUTC()
      .toISO()}`,
  );
  console.log(
    `    Last period rows length: ${lastScanResult.lastPeriodRows.length}`,
  );
}

type ScanResult = {
  path: string;
  isContinuous: boolean;
  lastPeriodRows: string[][];
  lastPeriodDateTime: DateTime;
};

export async function csvDownloadScan(
  path: string,
  dateIndex: number,
  normalizatingUnit: TimeSeriesLookupNormalizingUnit,
  previousScanResult?: ScanResult,
): Promise<ScanResult> {
  let trackingDateTime: DateTime | null = null;
  let rows: string[][] = [];

  let isCheckingContinuity = previousScanResult !== undefined;
  let isContinuous = true;

  return new Promise<ScanResult>((resolve, reject) => {
    fs.createReadStream(path)
      .pipe(parse({ delimiter: ",", fromLine: 2 }))
      .on("data", (row) => {
        const rowTime = DateTime.fromSQL(row[dateIndex]);
        if (trackingDateTime === null) {
          trackingDateTime = rowTime.startOf(normalizatingUnit);

          if (isCheckingContinuity) {
            if (trackingDateTime !== previousScanResult!.lastPeriodDateTime) {
              isContinuous = false;
            }
          }
        }
        if (
          trackingDateTime.startOf(normalizatingUnit) <
          rowTime.startOf(normalizatingUnit)
        ) {
          if (isCheckingContinuity) {
            isCheckingContinuity = false;
            if (!_.isEqual(previousScanResult!.lastPeriodRows, rows)) {
              // Check each of the last scan results rows
              const lastPeriodRows = previousScanResult!.lastPeriodRows;
              if (lastPeriodRows.length < 1) {
                console.warn(
                  `continuity of file is ambiguous between ${
                    previousScanResult!.path
                  } and ${path}`,
                );
                isContinuous = false;
              } else {
                for (let i = 0; i < lastPeriodRows.length; i++) {
                  if (!_.isEqual(lastPeriodRows[i], rows[i])) {
                    isContinuous = false;
                    break;
                  }
                }
              }
            }
          }
          rows = [];
          trackingDateTime = rowTime;
        }
        if (trackingDateTime > rowTime) {
          return reject(
            new Error(
              "invalid data it must be date time ordered (ascending at the moment)",
            ),
          );
        }

        // Keep the current set of rows until we hit the end or we change the
        // trackingDateTime
        rows.push(row);
      })
      .on("end", () => {
        if (!trackingDateTime) {
          return reject(new Error("there are no rows in this csv"));
        }

        resolve({
          path: path,
          // If there wasn't a previous file then we're ok
          isContinuous: previousScanResult === undefined ? true : isContinuous,
          lastPeriodDateTime: trackingDateTime,
          lastPeriodRows: rows,
        });
      });
  });
}
