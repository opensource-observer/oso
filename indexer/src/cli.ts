#!/usr/bin/env node
import yargs from "yargs";
import { hideBin } from "yargs/helpers";
import { handleError } from "./utils/error.js";
import {
  ImportOssDirectoryArgs,
  importOssDirectory,
} from "./collectors/import-oss-directory.js";
import { initializeDataSource } from "./db/data-source.js";
import {
  SchedulerArgs,
  SchedulerManualArgs,
  SchedulerQueueAllArgs,
  SchedulerQueueBackfill,
  SchedulerQueueJobArgs,
  SchedulerWorkerArgs,
  configure,
} from "./scheduler/index.js";
import { logger } from "./utils/logger.js";
import { csvCommandGroup } from "./scripts/manual-csv-import-helper.js";
import { duneCommandGroup } from "./scripts/manual-dune-tools.js";
import { artifactsCommandGroup } from "./scripts/artifact-management.js";
import { IExecutionSummary } from "./scheduler/types.js";
import { coerceDateTime, coerceDateTimeOrNow } from "./utils/cli.js";
import { dbUtilitiesCommandGroup } from "./scripts/db-utilities.js";

//const callLibrary = async <Args>(
//  func: EventSourceFunction<Args>,
//  args: Args,
//): Promise<void> => {
// TODO: handle ApiReturnType properly and generically here
//  const result = await func(args);
//  console.log(result);
//};

function outputError(err: unknown) {
  logger.info(err);
  try {
    logger.error(JSON.stringify(err));
    // eslint-disable-next-line no-restricted-properties
    console.error(err);
  } catch (_e) {
    logger.error("Cannot stringify error.");
    logger.error(err);
    // eslint-disable-next-line no-restricted-properties
    console.error(err);
  }
}

function handleExecutionSummary(execSummary: IExecutionSummary) {
  logger.info(`--------------Completed manual run---------------`);
  logger.info("   Collection Stats:");
  logger.info(`       ${execSummary.errorCount()} errors`);
  logger.info(
    `       ${execSummary.successfulArtifacts()} artifacts committed`,
  );
  logger.info(`       ${execSummary.failedArtifacts()} artifacts failed`);
  if (execSummary.hasErrors()) {
    if (execSummary.errors.length > 0) {
      logger.info(`General errors (not by artifact):`);
      for (const err of execSummary.errors) {
        outputError(err);
      }
    }
    if (execSummary.failedArtifacts() > 0) {
      for (const artifactSummary of execSummary.artifactSummaries) {
        const artifact = artifactSummary.artifact;
        logger.info(
          `Errors for Artifact[name=${artifact.name}, namespace=${artifact.namespace}]`,
        );
        for (const err of artifactSummary.results.errors) {
          outputError(err);
        }
      }
    }
    process.exit(1);
  }
  process.exit(0);
}

/**
 * When adding a new fetcher, please remember to add it to both this registry and yargs
 */
export const FETCHER_REGISTRY = [
  //NpmDownloadsInterface,
];
const cli = yargs(hideBin(process.argv))
  .middleware(async () => {
    // Initialize the database before operations
    await initializeDataSource();
  })
  .option("yes", {
    type: "boolean",
    describe: "Automatic yes to all prompts",
    default: false,
  })
  .option("cache-dir", {
    type: "string",
    describe: "sets the path to the cache directory",
    default: "/tmp/oso/cache",
  })
  .option("run-dir", {
    type: "string",
    describe: "sets the path to the run directory",
    default: "/tmp/oso/run",
  })
  .command<ImportOssDirectoryArgs>(
    "importOssDirectory",
    "Import projects and collections from 'oss-directory'",
    (yags) => {
      yags.option("skip-existing", {
        type: "boolean",
        default: false,
      });
    },
    (argv) => handleError(importOssDirectory(argv)),
  )
  .command<Record<string, never>>(
    "csv <subcommand>",
    "subcommand for csv related tools",
    (yargs) => {
      csvCommandGroup(yargs);
    },
  )
  .command<Record<string, never>>(
    "dune <subcommand>",
    "subcommand for dune related tools",
    (yargs) => {
      duneCommandGroup(yargs);
    },
  )
  .command<Record<string, never>>(
    "artifacts <subcommand>",
    "subcommand for artifacts related tools",
    (yargs) => {
      artifactsCommandGroup(yargs);
    },
  )
  .command<Record<string, never>>(
    "db-utils <subcommand>",
    "subcommand for artifacts related tools",
    (yargs) => {
      dbUtilitiesCommandGroup(yargs);
    },
  )
  .command<SchedulerArgs>(
    "scheduler <subcommand>",
    "scheduler commands",
    (yags) => {
      yags.option("overwrite-existing-events", {
        type: "boolean",
        default: false,
      });
      yags.option("recorder-timeout-ms", {
        type: "number",
        default: 600000,
      });
      yags.option("recorder-connections", {
        type: "number",
        default: 10,
      });
      yags
        .command<SchedulerManualArgs>(
          "manual <collector>",
          "manually execute a scheduler run",
          (yags) => {
            yags
              .positional("collector", {
                describe: "the name of the collector to execute",
              })
              .option("start-date", {
                type: "string",
                describe: "start-date for the manual run",
              })
              .coerce("start-date", coerceDateTime)
              .option("end-date", {
                type: "string",
                describe: "start-date for the manual run",
              })
              .coerce("end-date", coerceDateTime)
              .option("execution-mode", {
                type: "string",
                choices: ["all-at-once", "progressive"],
              })
              .option("reindex", {
                type: "boolean",
                default: false,
              });
          },
          async (args) => {
            const scheduler = await configure(args);

            const execSummary = await scheduler.executeCollector(
              args.collector,
              {
                range: {
                  startDate: args.startDate,
                  endDate: args.endDate,
                },
                mode: args.executionMode,
                reindex: args.reindex,
              },
            );
            handleExecutionSummary(execSummary);
          },
        )
        .command<SchedulerWorkerArgs>(
          "worker <group>",
          "run the worker",
          (yags) => {
            yags
              .positional("group", {
                describe: "the group to execute",
                type: "string",
              })
              .option("resume-with-lock", {
                describe: "resume with the lock on disk?",
                type: "boolean",
                default: false,
              });
          },
          async (args) => {
            const scheduler = await configure(args);
            const execSummary = await scheduler.runWorker(
              args.group,
              args.resumeWithLock,
            );
            handleExecutionSummary(execSummary);
          },
        )
        .command<SchedulerQueueAllArgs>(
          "queue [base-date]",
          "schedule workers into the queue",
          (yags) => {
            yags
              .positional("base-date", {
                describe: "the date to start scheduling from",
                type: "string",
              })
              .coerce("base-date", coerceDateTimeOrNow);
          },
          async (args) => {
            const scheduler = await configure(args);
            await scheduler.queueAll(args.baseDate);
          },
        )
        .command("job <job-subcommand>", "job tools", (yags) => {
          yags
            .command<SchedulerQueueJobArgs>(
              "create <collector>",
              "queue a job manually",
              (yags) => {
                yags
                  .positional("collector", {
                    describe: "the collector",
                    type: "string",
                  })
                  .option("base-date", {
                    type: "string",
                    describe: "start-date for the manual run",
                  })
                  .coerce("base-date", coerceDateTime)
                  .option("start-date", {
                    type: "string",
                    describe: "start-date for the manual run",
                  })
                  .coerce("start-date", coerceDateTime)
                  .option("end-date", {
                    type: "string",
                    describe: "start-date for the manual run",
                  })
                  .coerce("end-date", coerceDateTime)
                  .demandOption(["base-date", "start-date", "end-date"]);
              },
              async (args) => {
                const scheduler = await configure(args);
                await scheduler.queueEventJob(args.collector, args.baseDate, {
                  startDate: args.startDate,
                  endDate: args.endDate,
                });
              },
            )
            .command<SchedulerQueueBackfill>(
              "backfill <collector>",
              "create a backfill job",
              (yags) => {
                yags
                  .positional("collector", {
                    describe: "the collector",
                    type: "string",
                  })
                  .option("start-date", {
                    type: "string",
                    describe: "start-date for the backfill scheduling",
                  })
                  .coerce("start-date", coerceDateTime)
                  .option("end-date", {
                    type: "string",
                    describe: "end-date for the backfill scheduling",
                  })
                  .coerce("end-date", coerceDateTimeOrNow)
                  .option("backfill-interval-days", {
                    type: "number",
                    default: 0,
                  })
                  .demandOption(["start-date"]);
              },
              async (args) => {
                const scheduler = await configure(args);
                await scheduler.queueBackfill(
                  args.collector,
                  args.startDate,
                  args.backfillIntervalDays,
                );
              },
            )
            .command<SchedulerArgs>(
              "clean-lock",
              "clean the lock for a job execution if it exists",
              (_yags) => {},
              async (args) => {
                const scheduler = await configure(args);
                await scheduler.cleanLock();
              },
            );
        });
    },
  )
  .demandCommand()
  .strict()
  .help("h")
  .alias("h", "help");

function main() {
  // This was necessary to satisfy the es-lint no-floating-promises check.
  const promise = cli.parse() as Promise<unknown>;
  promise.catch((err) => {
    logger.error("error caught running the cli", err);
  });
}

main();
