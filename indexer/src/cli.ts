#!/usr/bin/env node
import yargs from "yargs";
import { hideBin } from "yargs/helpers";
import { RunAutocrawlArgs, runAutocrawl } from "./actions/autocrawl.js";
import { handleError } from "./utils/error.js";
import { CommonArgs, EventSourceFunction } from "./utils/api.js";
//import { NpmDownloadsArgs, NpmDownloadsInterface } from "./events/npm.js";
import { DateTime } from "luxon";
import {
  ImportOssDirectoryArgs,
  importOssDirectory,
} from "./actions/oss-directory.js";
import { AppDataSource } from "./db/data-source.js";
// import {
//   importDailyContractUsage,
// } from "./actions/dune/index.js";
// import { LoadCommits, loadCommits } from "./actions/github/fetch/commits.js";
// import {
//   LoadRepositoryFollowers,
//   loadRepositoryFollowers,
// } from "./actions/github/fetch/repo-followers.js";
// import {
//   LoadPullRequests,
//   loadPullRequests,
// } from "./actions/github/fetch/pull-requests.js";
//import { SchedulerArgs, defaults } from "./scheduler/index.js";

const callLibrary = async <Args>(
  func: EventSourceFunction<Args>,
  args: Args,
): Promise<void> => {
  // TODO: handle ApiReturnType properly and generically here
  const result = await func(args);
  console.log(result);
};

/**
 * When adding a new fetcher, please remember to add it to both this registry and yargs
 */
export const FETCHER_REGISTRY = [
  //NpmDownloadsInterface,
];
yargs(hideBin(process.argv))
  .middleware(async () => {
    // Initialize the database
    await AppDataSource.initialize();
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
    default: "/tmp/oso",
  })
  .command<ImportOssDirectoryArgs>(
    "importOssDirectory",
    "Import projects and collections from 'oss-directory'",
    (yags) => {
      yags.option("skipExisting", { type: "boolean" });
    },
    (argv) => handleError(importOssDirectory(argv)),
  )
  // .command<ImportDailyContractUsage>(
  //   "importDailyContractUsage",
  //   "Manually import contract usage statistics from dune",
  //   (yags) => {
  //     yags
  //       .option("skipExisting", { type: "boolean" })
  //       .option("interval", { type: "number" })
  //       .option("base-date", { type: "string", default: "" })
  //       .coerce("base-date", (arg) => {
  //         if (arg === "") {
  //           return DateTime.now();
  //         }
  //         return DateTime.fromISO(arg);
  //       });
  //   },
  //   (argv) => handleError(importDailyContractUsage(argv)),
  // )
  // .command<LoadCommits>(
  //   "loadCommits",
  //   "Manually import commits",
  //   (yags) => {
  //     yags.option("skipExisting", { type: "boolean" });
  //   },
  //   (argv) => handleError(loadCommits(argv)),
  // )
  // .command<LoadRepositoryFollowers>(
  //   "loadRepositoryFollowers",
  //   "Manually import commits",
  //   (yags) => {
  //     yags.option("skipExisting", { type: "boolean" });
  //   },
  //   (argv) => handleError(loadRepositoryFollowers(argv)),
  // )
  // .command<LoadPullRequests>(
  //   "loadPullRequests",
  //   "Manually import pull requests",
  //   (yags) => {
  //     yags.option("skipExisting", { type: "boolean" });
  //   },
  //   (argv) => handleError(loadPullRequests(argv)),
  // )
  .command<RunAutocrawlArgs>(
    "runAutocrawl",
    "Iterate over EventSourcePointer table and update all data marked for autocrawl",
    (yags) => {
      yags;
    },
    (argv) => handleError(runAutocrawl(argv)),
  )
  // .command<NpmDownloadsArgs>(
  //   NpmDownloadsInterface.command,
  //   "Fetch NPM downloads",
  //   (yags) => {
  //     yags
  //       .option("name", {
  //         type: "string",
  //         describe: "Package name",
  //       })
  //       .demandOption(["name"]);
  //   },
  //   (argv) => handleError(callLibrary(NpmDownloadsInterface.func, argv)),
  // )
  // .command<SchedulerArgs>(
  //   "scheduler <collector>",
  //   "Runs a manual execution",
  //   (yags) => {
  //     yags
  //       .positional("collector", { describe: "the collector to execute" })
  //       .option("start-date", { type: "string", default: "" })
  //       .coerce("start-date", (arg) => {
  //         if (arg === "") {
  //           return DateTime.now().startOf("day").minus({ days: 9 });
  //         }
  //         return DateTime.fromISO(arg);
  //       })
  //       .option("end-date", { type: "string", default: "" })
  //       .coerce("end-date", (arg) => {
  //         if (arg === "") {
  //           return DateTime.now().startOf("day").minus({ days: 2 });
  //         }
  //         return DateTime.fromISO(arg);
  //       })
  //       .option("batch-size", { type: "number", default: 5000 });
  //   },
  //   (argv) => handleError(defaults(argv)),
  // )
  .demandCommand()
  .strict()
  .help("h")
  .alias("h", "help")
  .parse();
