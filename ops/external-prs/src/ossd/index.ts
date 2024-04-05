import tmp from "tmp-promise";
import { Argv } from "yargs";
import { handleError } from "../utils/error.js";
import { logger } from "../utils/logger.js";
import { BaseArgs } from "../base.js";
import { loadData, Project, Collection } from "oss-directory";
import duckdb from "duckdb";
import * as util from "util";
import * as fs from "fs";
import * as path from "path";
import * as repl from "repl";
import columnify from "columnify";

// async withComparison<T>(compareFn: (db: duckdb.Database) => Promise<T>): Promise<T> {
//   return await tmp.withDir(
//     async (t) => {
//       // Load the data
//       const main = await loadData(this.mainDataPath);
//       const pr = await loadData(this.prDataPath);
//       const db = new duckdb.Database(':memory:');

//       const tablesToCompare: { [table: string]: Project[] | Collection[] } = {
//         "main_projects": main.projects,
//         "main_collections": main.collections,
//         "pr_projects": pr.projects,
//         "pr_collections": pr.collections,
//       }

//       for (const table in tablesToCompare) {
//         // Dump the data into the work path as JSONL files
//         const dumpPath = path.resolve(path.join(t.path, `${table}.json`));
//         await this.jsonlExport(dumpPath, tablesToCompare[table]);

//         // Load that data into duckdb
//         db.run(`
//           CREATE TABLE ${table} AS
//             SELECT *
//           FROM read_json_auto('${dumpPath}');
//         `);
//       }

//       // Run the comparison
//       return await compareFn(db);
//     },
//     { unsafeCleanup: true },
//   )
// }

function jsonlExport<T>(path: string, arr: Array<T>): Promise<void> {
  return new Promise((resolve, reject) => {
    const stream = fs.createWriteStream(path, "utf-8");
    for (const item of arr) {
      stream.write(JSON.stringify(item));
      stream.write("\n");
    }
    stream.close((err) => {
      if (err) {
        return reject(err);
      }
      return resolve();
    });
  });
}

export function ossdSubcommands(yargs: Argv) {
  yargs.command<ValidatePRArgs>(
    "validate-pr <pr> <sha> <main-path> <pr-path>",
    "validate changes for an OSSD PR",
    (yags) => {
      yags.positional("pr", {
        type: "number",
        description: "pr number",
      });
      yags.positional("sha", {
        type: "string",
        description: "The sha of the pull request",
      });
      yags.positional("main-path", {
        type: "string",
        description: "The path to the main branch checkout",
      });
      yags.positional("path-path", {
        type: "string",
        description: "The path to the pr checkout",
      });
      yags.option("repl", {
        type: "boolean",
        description: "Start a repl for exploration on the data",
        default: false,
      });
      yags.boolean("repl");
    },
    (args) => handleError(validatePR(args)),
  );
}

interface ValidatePRArgs extends BaseArgs {
  pr: string;
  sha: string;
  mainPath: string;
  prPath: string;
  repl: boolean;
}

async function validatePR(args: ValidatePRArgs) {
  logger.info({
    message: "validating the pull request",
    repo: args.repo,
    sha: args.sha,
    pr: args.pr,
  });

  //const app = args.app;

  const main = await loadData(args.mainPath);
  const pr = await loadData(args.prPath);

  const db = new duckdb.Database(":memory:");

  const tablesToCompare: { [table: string]: Project[] | Collection[] } = {
    main_projects: main.projects,
    main_collections: main.collections,
    pr_projects: pr.projects,
    pr_collections: pr.collections,
  };

  const dbAll = util.promisify(db.all.bind(db));
  return tmp.withDir(
    async (t) => {
      for (const table in tablesToCompare) {
        const dumpPath = path.resolve(path.join(t.path, `${table}.json`));
        await jsonlExport(dumpPath, tablesToCompare[table]);
        // Dump the data into the work path as JSONL files
        //const arrowTable = arrow.tableFromJSON(JSON.parse(JSON.stringify(tablesToCompare[table])));

        const res = await dbAll(`
          CREATE TABLE ${table} AS
          SELECT *
          FROM read_json_auto('${dumpPath}');
        `);
        logger.info({
          message: "created table",
          tableName: table,
          queryResponse: res,
        });
      }
      const server = repl.start();
      if (args.repl) {
        server.context.$db = {
          // Setup raw access to the duckdb api via db
          raw: db,
          // Setup a convenience command that runs queries
          q: async (query: string) => {
            const res = await dbAll(query);
            console.log(columnify(res as Record<string, any>[]));
            return res;
          },
        };
        await new Promise<void>((resolve, reject) => {
          server.on("exit", () => {
            resolve();
          });
          server.on("SIGINT", () => {
            reject(new Error("SIGINT?"));
          });
        });
      }

      // List all the new blockchain artifacts
      // List all the new code artifacts
      // List all the new package artifacts

      // List all the removed blockchain artifacts
      // List all the removed code artifacts
      // List all the removed package artifacts

      // List all the changed blockchain artifacts
      // List all the changed code artifacts
      // List all the changed package artifacts
    },
    { unsafeCleanup: true },
  );
}
