#!/usr/bin/env node
import yargs from "yargs";
import { DateTime } from "luxon";
import { hideBin } from "yargs/helpers";
import { RunAutocrawlArgs, runAutocrawl } from "./actions/autocrawl.js";
import { handleError } from "./utils/error.js";
import {
  ImportOssDirectoryArgs,
  importOssDirectory,
} from "./actions/oss-directory.js";
import { initializeDataSource } from "./db/data-source.js";
import {
  SchedulerArgs,
  SchedulerManualArgs,
  SchedulerQueueAllArgs,
  SchedulerQueueJobArgs,
  SchedulerWorkerArgs,
  configure,
} from "./scheduler/index.js";
import { logger } from "./utils/logger.js";
import { csvCommandGroup } from "./scripts/manual-csv-import-helper.js";
import { duneCommandGroup } from "./scripts/manual-dune-tools.js";
import { artifactsCommandGroup } from "./scripts/artifact-management.js";

//const callLibrary = async <Args>(
//  func: EventSourceFunction<Args>,
//  args: Args,
//): Promise<void> => {
// TODO: handle ApiReturnType properly and generically here
//  const result = await func(args);
//  console.log(result);
//};

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
  .option("autocrawl", {
    type: "boolean",
    describe: "Mark the query for auto-crawling",
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
  .command<RunAutocrawlArgs>(
    "runAutocrawl",
    "Iterate over EventSourcePointer table and update all data marked for autocrawl",
    (yags) => {
      yags;
    },
    (argv) => handleError(runAutocrawl(argv)),
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
      const dateConverter = (input: string) => {
        const date = DateTime.fromISO(input).toUTC();
        if (!date.isValid) {
          throw new Error(`input "${input}" is not a valid date`);
        }
        return date;
      };
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
              .coerce("start-date", dateConverter)
              .option("end-date", {
                type: "string",
                describe: "start-date for the manual run",
              })
              .coerce("end-date", dateConverter)
              .demandOption(["start-date", "end-date"])
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
                startDate: args.startDate,
                endDate: args.endDate,
              },
              args.executionMode,
              args.reindex,
            );

            logger.info(`--------------Completed manual run---------------`);
            logger.info("   Collection Stats:");
            logger.info(`       ${execSummary.errors.length} errors`);
            logger.info(
              `       ${execSummary.artifactSummaries.length} artifacts committed`,
            );
            if (execSummary.errors.length > 0) {
              for (const err of execSummary.errors) {
                logger.info(err);
                try {
                  logger.error(JSON.stringify(err));
                } catch (_e) {
                  logger.error("Cannot stringify error.");
                  logger.error(err);
                }
              }
              process.exit(1);
            }
            process.exit(0);
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
            logger.info(`--------------Completed job---------------`);
            logger.info("   Collection Stats:");
            logger.info(`       ${execSummary.errors.length} errors`);
            logger.info(
              `       ${execSummary.artifactSummaries.length} artifacts committed`,
            );
            if (execSummary.errors.length > 0) {
              process.exit(1);
            }
            process.exit(0);
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
              .coerce("base-date", (input: string) => {
                if (input) {
                  return dateConverter(input);
                }
                return DateTime.now();
              });
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
                  .coerce("base-date", dateConverter)
                  .option("start-date", {
                    type: "string",
                    describe: "start-date for the manual run",
                  })
                  .coerce("start-date", dateConverter)
                  .option("end-date", {
                    type: "string",
                    describe: "start-date for the manual run",
                  })
                  .coerce("end-date", dateConverter)
                  .demandOption(["base-date", "start-date", "end-date"]);
              },
              async (args) => {
                const scheduler = await configure(args);
                await scheduler.queueJob(args.collector, args.baseDate, {
                  startDate: args.startDate,
                  endDate: args.endDate,
                });
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
