import tmp from "tmp-promise";
import { fileURLToPath } from "node:url";
import { Argv } from "yargs";
import { handleError } from "../utils/error.js";
import { logger } from "../utils/logger.js";
import { BaseArgs } from "../base.js";
import { loadData, Project, Collection } from "oss-directory";
import duckdb from "duckdb";
import * as util from "util";
import * as fs from "fs";
import * as fsPromise from "fs/promises";
import * as path from "path";
import * as repl from "repl";
import columnify from "columnify";
import mustache from "mustache";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
// Should map to the tables field in ./metadata/databases/databases.yaml

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
  yargs.command<OSSDirectoryPullRequestArgs>(
    "list-changes <pr> <sha> <main-path> <pr-path>",
    "list changes for an OSSD PR",
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
      yags.option("duckdb-path", {
        type: "string",
        description: "The duckdb path. Defaults to using in memory storage",
      });
    },
    (args) => handleError(listPR(args)),
  );
  yargs.command<OSSDirectoryPullRequestArgs>(
    "validate-pr <pr> <sha> <main-path> <pr-path>",
    "Validate changes for an OSSD PR",
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
      yags.option("duckdb-path", {
        type: "string",
        description: "The duckdb path. Defaults to using in memory storage",
      });
    },
    (args) => handleError(validatePR(args)),
  );
}

interface OSSDirectoryPullRequestArgs extends BaseArgs {
  pr: string;
  sha: string;
  mainPath: string;
  prPath: string;
  repl: boolean;
  duckdbPath: string;
}

async function runParameterizedQuery(
  db: duckdb.Database,
  name: string,
  params?: Record<string, unknown>,
) {
  params = params || {};
  const raw = await fsPromise.readFile(
    path.join(__dirname, "queries", `${name}.sql`),
    "utf-8",
  );
  const query = mustache.render(raw, params);
  logger.info({
    message: "running query",
    query: query,
  });
  const dbAll = util.promisify(db.all.bind(db));
  return dbAll(query);
}

type ProjectSummary = {
  project_slug: string;
  status: string;
  blockchain_added: number;
  blockchain_removed: number;
  blockchain_unchanged: number;
  blockchain_unique_added: number;
  blockchain_unique_removed: number;
  blockchain_unique_unchanged: number;
  code_added: number;
  code_removed: number;
  code_unchanged: number;
  package_added: number;
  package_removed: number;
  package_unchanged: number;
};

type CodeStatus = {
  project_slug: string;
  code_url: string;
  status: string;
};

type PackageStatus = {
  project_slug: string;
  package_url: string;
  status: string;
};

type BlockchainStatus = {
  project_slug: string;
  address: string;
  tag: string;
  network: string;
  project_relation_status: string;
  address_status: string;
  network_status: string;
  network_tag_status: string;
};

type BlockchainValidationItem = {
  address: string;
  tags: string[];
  networks: string[];
};

type ChangeSummary = {
  projects: ProjectSummary[];
  artifacts: {
    blockchain: BlockchainStatus[];
    package: PackageStatus[];
    code: CodeStatus[];
  };
  toValidate: {
    blockchain: BlockchainValidationItem[];
  };
};

class OSSDirectoryPullRequest {
  private db: duckdb.Database;
  private args: OSSDirectoryPullRequestArgs;
  private changes: ChangeSummary;

  static async init(args: OSSDirectoryPullRequestArgs) {
    const pr = new OSSDirectoryPullRequest(args);
    await pr.initialize();
    return pr;
  }

  private constructor(args: OSSDirectoryPullRequestArgs) {
    this.args = args;
  }

  private async initialize() {
    const args = this.args;

    logger.info({
      message: "setting up the pull request for comparison",
      repo: args.repo,
      sha: args.sha,
      pr: args.pr,
    });

    //const app = args.app;

    const main = await loadData(args.mainPath);
    const pr = await loadData(args.prPath);

    const duckdbPath = args.duckdbPath || ":memory:";

    const db = new duckdb.Database(duckdbPath);
    this.db = db;

    const tablesToCompare: { [table: string]: Project[] | Collection[] } = {
      main_projects: main.projects,
      main_collections: main.collections,
      pr_projects: pr.projects,
      pr_collections: pr.collections,
    };

    const dbAll = util.promisify(db.all.bind(db));
    console.log(__dirname);
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

        // Implement a poor man's dbt. We should just use dbt but this will work
        // for now without muddying up more things with python + javascript
        // requirements
        await runParameterizedQuery(db, "projects_by_collection", {
          source: "main",
        });
        await runParameterizedQuery(db, "projects_by_collection", {
          source: "pr",
        });
        await runParameterizedQuery(db, "blockchain_artifacts", {
          source: "main",
        });
        await runParameterizedQuery(db, "blockchain_artifacts", {
          source: "pr",
        });
        await runParameterizedQuery(db, "code_artifacts", {
          source: "main",
        });
        await runParameterizedQuery(db, "code_artifacts", {
          source: "pr",
        });
        await runParameterizedQuery(db, "package_artifacts", {
          source: "main",
        });
        await runParameterizedQuery(db, "package_artifacts", {
          source: "pr",
        });

        await runParameterizedQuery(db, "project_status");
        await runParameterizedQuery(db, "projects_by_collection_status");
        await runParameterizedQuery(db, "blockchain_status");
        await runParameterizedQuery(db, "package_status");
        await runParameterizedQuery(db, "code_status");
        await runParameterizedQuery(db, "project_summary");

        const runQuery = async (
          query: string,
          includeResponse: boolean = false,
        ) => {
          const res = await dbAll(query);
          console.log("");
          console.log(
            columnify(res as Record<string, any>[], {
              truncate: true,
              maxWidth: 20,
            }),
          );
          console.log("");
          if (!includeResponse) {
            return;
          } else {
            return res;
          }
        };

        const changes: ChangeSummary = {
          projects: (await runParameterizedQuery(
            db,
            "changed_projects",
          )) as ProjectSummary[],
          artifacts: {
            blockchain: (await runParameterizedQuery(
              db,
              "changed_blockchain_artifacts",
            )) as BlockchainStatus[],
            code: (await runParameterizedQuery(
              db,
              "changed_code_artifacts",
            )) as CodeStatus[],
            package: (await runParameterizedQuery(
              db,
              "changed_package_artifacts",
            )) as PackageStatus[],
          },
          toValidate: {
            blockchain: (await runParameterizedQuery(
              db,
              "changed_blockchain_artifacts_to_validate",
            )) as BlockchainValidationItem[],
          },
        };
        this.changes = changes;

        // For simple debugging purposes we provide a REPL to explore the data.
        if (args.repl) {
          const server = repl.start();
          server.context.$db = {
            // Setup raw access to the duckdb api via db
            raw: db,
            // Setup a convenience command that runs queries
            $: async (query: string) => {
              await runQuery(query);
            },
            $$: async (query: string) => {
              return await runQuery(query, true);
            },
          };
          server.context.changes = changes;
          await new Promise<void>((resolve, reject) => {
            server.on("exit", () => {
              resolve();
            });
            server.on("SIGINT", () => {
              reject(new Error("SIGINT?"));
            });
          });
        }
      },
      { unsafeCleanup: true },
    );
  }

  async list() {
    logger.info(
      "Enumerate the changes as a comment on the PR - without full bigquery access",
    );
  }

  async validate() {
    logger.info({
      message: "validating the pull request",
      repo: this.args.repo,
      sha: this.args.sha,
      pr: this.args.pr,
    });
  }
}

async function listPR(args: OSSDirectoryPullRequestArgs) {
  const pr = await OSSDirectoryPullRequest.init(args);
  await pr.list();
}

async function validatePR(args: OSSDirectoryPullRequestArgs) {
  const pr = await OSSDirectoryPullRequest.init(args);
  await pr.validate();
}
