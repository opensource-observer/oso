import tmp from "tmp-promise";
import { fileURLToPath } from "node:url";
import { Argv } from "yargs";
import { handleError } from "../utils/error.js";
import { logger } from "../utils/logger.js";
import { BaseArgs, CommmentCommandHandler } from "../base.js";
import {
  loadData,
  Project,
  Collection,
  BlockchainNetwork,
  BlockchainTag,
} from "oss-directory";
import duckdb from "duckdb";
import * as util from "util";
import * as fs from "fs";
import * as path from "path";
import * as repl from "repl";
import columnify from "columnify";
import {
  DefiLlamaValidator,
  EVMNetworkValidator,
  EthereumContractsV0Validator,
  ArbitrumContractsV0Validator,
  BaseContractsV0Validator,
  OptimismContractsV0Validator,
  AnyEVMContractsV0Validator,
} from "@opensource-observer/oss-artifact-validators";
import { uncheckedCast } from "@opensource-observer/utils";
import { CheckConclusion, CheckStatus } from "../checks.js";
import { GithubOutput } from "../github.js";
import { renderMustacheFromFile } from "./templating.js";
import { ValidationResults } from "./validation-results.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
function relativeDir(...args: string[]) {
  return path.join(__dirname, ...args);
}

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

interface ParseCommentArgs extends BaseArgs {
  // Comment ID
  comment: number;
  // Output filename
  output: string;
  login: string;
}

export function ossdSubcommands(yargs: Argv) {
  yargs
    .command<OSSDirectoryPullRequestArgs>(
      "list-changes <pr> <sha> <main-path> <pr-path>",
      "list changes for an OSSD PR",
      (yags) => {
        yags
          .positional("pr", {
            type: "number",
            description: "pr number",
          })
          .positional("sha", {
            type: "string",
            description: "The sha of the pull request",
          })
          .positional("main-path", {
            type: "string",
            description: "The path to the main branch checkout",
          })
          .positional("path-path", {
            type: "string",
            description: "The path to the pr checkout",
          })
          .option("repl", {
            type: "boolean",
            description: "Start a repl for exploration on the data",
            default: false,
          })
          .boolean("repl")
          .option("duckdb-path", {
            type: "string",
            description: "The duckdb path. Defaults to using in memory storage",
          })
          .option("duckdb-memory-limit", {
            type: "string",
            description: "duckdb memory limit (needed for github actions)",
            default: "",
          })
          .option("duckdb-memory-limit", {
            type: "string",
            description: "duckdb memory limit (needed for github actions)",
            default: "",
          });
      },
      (args) => handleError(listPR(args)),
    )
    .command<ValidatePRArgs>(
      "validate-pr <pr> <sha> <main-path> <pr-path>",
      "Validate changes for an OSSD PR",
      (yags) => {
        yags
          .positional("pr", {
            type: "number",
            description: "pr number",
          })
          .positional("sha", {
            type: "string",
            description: "The sha of the pull request",
          })
          .positional("main-path", {
            type: "string",
            description: "The path to the main branch checkout",
          })
          .positional("path-path", {
            type: "string",
            description: "The path to the pr checkout",
          })
          .option("repl", {
            type: "boolean",
            description: "Start a repl for exploration on the data",
            default: false,
          })
          .boolean("repl")
          .option("duckdb-path", {
            type: "string",
            description: "The duckdb path. Defaults to using in memory storage",
          })
          .option("duckdb-memory-limit", {
            type: "string",
            description: "duckdb memory limit (needed for github actions)",
            default: "",
          })
          .option("duckdb-memory-limit", {
            type: "string",
            description: "duckdb memory limit (needed for github actions)",
            default: "",
          })
          .option("mainnet-rpc-url", {
            type: "string",
            description: "Ethereum Mainnet RPC URL",
            demandOption: true,
          })
          .option("arbitrum-rpc-url", {
            type: "string",
            description: "Ethereum Mainnet RPC URL",
            demandOption: true,
          })
          .option("base-rpc-url", {
            type: "string",
            description: "Base RPC URL",
            demandOption: true,
          })
          .option("optimism-rpc-url", {
            type: "string",
            description: "Optimism RPC URL",
            demandOption: true,
          });
      },
      (args) => handleError(validatePR(args)),
    )
    .command<ParseCommentArgs>(
      "parse-comment <comment> <output>",
      "subcommand for parsing a deploy comment",
      (yags) => {
        yags.positional("comment", {
          type: "number",
          description: "Comment ID",
        });
        yags.positional("output", {
          type: "string",
          description: "The output file",
        });
      },
      (args) => handleError(parseOSSDirectoryComments(args)),
    );
}

interface OSSDirectoryPullRequestArgs extends BaseArgs {
  pr: number;
  sha: string;
  mainPath: string;
  prPath: string;
  repl: boolean;
  duckdbPath: string;
  duckdbMemoryLimit: string;
}

interface RpcUrlArgs {
  mainnetRpcUrl: string;
  arbitrumRpcUrl: string;
  baseRpcUrl: string;
  optimismRpcUrl: string;
}

type ValidatePRArgs = OSSDirectoryPullRequestArgs & RpcUrlArgs;

async function runParameterizedQuery(
  db: duckdb.Database,
  name: string,
  params?: Record<string, unknown>,
) {
  params = params || {};
  const queryPath = relativeDir("queries", `${name}.sql`);
  const query = await renderMustacheFromFile(queryPath, params);
  logger.info({
    message: `running query: ${name}`,
    query: query,
  });
  const dbAll = util.promisify(db.all.bind(db));
  return dbAll(query);
}

// | Projects             | {{ projects.existing }} {{ projects.added }} | {{projects.removed}} | {{ projects.updated }}
type ProjectSummary = {
  project_name: string;
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

type UrlStatus = {
  project_name: string;
  url_value: string;
  url_type: string;
  status: string;
};

type BlockchainStatus = {
  project_name: string;
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

type UrlItem = {
  // Full URL
  url_value: string;
  // The type of URL
  // e.g. GITHUB, NPM, DEFILLAMA, WEBSITE
  url_type: string;
};

type Summary = {
  added: number;
  removed: number;
  existing: number;
};

// type BlockchainSummary = Summary & {
//   unique_added: number;
//   removed_number: number;
// }

type ChangeSummary = {
  projects: ProjectSummary[];
  artifacts: {
    summary: Record<string, Summary>;
    status: {
      blockchain: BlockchainStatus[];
      url: UrlStatus[];
    };
    toValidate: {
      blockchain: BlockchainValidationItem[];
      defillama: UrlItem[];
    };
  };
};

class OSSDirectoryPullRequest {
  private db: duckdb.Database;
  private args: OSSDirectoryPullRequestArgs;
  private changes: ChangeSummary;
  private blockchainValidators: Partial<
    Record<BlockchainNetwork, EVMNetworkValidator>
  >;
  private defillamaValidator: DefiLlamaValidator;

  static async init(args: OSSDirectoryPullRequestArgs) {
    const pr = new OSSDirectoryPullRequest(args);
    await pr.initialize();
    return pr;
  }

  private constructor(args: OSSDirectoryPullRequestArgs) {
    this.args = args;
    this.blockchainValidators = {};
  }

  async loadValidators(urls: RpcUrlArgs) {
    this.defillamaValidator = new DefiLlamaValidator();
    this.blockchainValidators["any_evm"] = AnyEVMContractsV0Validator(
      urls.mainnetRpcUrl,
    );
    this.blockchainValidators["mainnet"] = EthereumContractsV0Validator(
      urls.mainnetRpcUrl,
    );
    this.blockchainValidators["arbitrum_one"] = ArbitrumContractsV0Validator(
      urls.arbitrumRpcUrl,
    );
    this.blockchainValidators["base"] = BaseContractsV0Validator(
      urls.baseRpcUrl,
    );
    this.blockchainValidators["optimism"] = OptimismContractsV0Validator(
      urls.optimismRpcUrl,
    );
  }

  async dbAll(query: string) {
    const dbAll = util.promisify(this.db.all.bind(this.db));
    return await dbAll(query);
  }

  async runParameterizedQuery(name: string, params?: Record<string, unknown>) {
    params = params || {};
    const queryPath = relativeDir("queries", `${name}.sql`);
    const query = await renderMustacheFromFile(queryPath, params);
    logger.info({
      message: `running query: ${name}`,
      query: query,
    });
    return this.dbAll(query);
  }

  // Run query with pretty output
  async runQuery(query: string, includeResponse: boolean = false) {
    const res = await this.dbAll(query);
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
  }

  private async initialize() {
    const args = this.args;

    logger.info({
      message: `setting up the pull request for comparison`,
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

    if (args.duckdbMemoryLimit !== "") {
      logger.info({
        message: `setting memory limit to ${args.duckdbMemoryLimit}`,
        memoryLimit: args.duckdbMemoryLimit,
      });
      await this.dbAll(`
      SET memory_limit = '${args.duckdbMemoryLimit}';
      `);
    }
    return tmp.withDir(
      async (t) => {
        for (const table in tablesToCompare) {
          const dumpPath = path.resolve(path.join(t.path, `${table}.json`));
          await jsonlExport(dumpPath, tablesToCompare[table]);
          // Dump the data into the work path as JSONL files
          //const arrowTable = arrow.tableFromJSON(JSON.parse(JSON.stringify(tablesToCompare[table])));

          const res = await this.dbAll(`
            CREATE TABLE ${table} AS
            SELECT *
            FROM read_json_auto('${dumpPath}');
          `);
          logger.info({
            message: `created table ${table}`,
            tableName: table,
            queryResponse: res,
          });
        }

        // Implement a poor man's dbt. We should just use dbt but this will work
        // for now without muddying up more things with python + javascript
        // requirements
        await this.runParameterizedQuery("projects_by_collection", {
          source: "main",
        });
        await this.runParameterizedQuery("projects_by_collection", {
          source: "pr",
        });
        await this.runParameterizedQuery("blockchain_artifacts", {
          source: "main",
        });
        await this.runParameterizedQuery("blockchain_artifacts", {
          source: "pr",
        });
        await this.runParameterizedQuery("url_artifacts", {
          source: "main",
        });
        await this.runParameterizedQuery("url_artifacts", {
          source: "pr",
        });

        await this.runParameterizedQuery("project_status");
        await this.runParameterizedQuery("projects_by_collection_status");
        await this.runParameterizedQuery("blockchain_status");
        await this.runParameterizedQuery("url_status");
        await this.runParameterizedQuery("artifacts_summary");
        await this.runParameterizedQuery("project_summary");

        const artifactsSummary = (await this.runQuery(
          "SELECT * FROM artifacts_summary",
          true,
        )) as {
          type: string;
          status: string;
          count: number;
          unique_count: number;
        }[];
        const summaries: Record<string, Summary> = {};
        for (const row of artifactsSummary) {
          if (!summaries[row.type]) {
            summaries[row.type] = {
              added: row.status == "ADDED" ? row.count : 0,
              removed: row.status == "REMOVED" ? row.count : 0,
              existing: row.status == "EXISTING" ? row.count : 0,
            };
          } else {
            if (row.status == "ADDED") {
              summaries[row.type].added = row.count;
            } else if (row.type == "REMOVED") {
              summaries[row.type].removed = row.count;
            } else {
              summaries[row.type].existing = row.count;
            }
          }
        }

        const changes: ChangeSummary = {
          projects: (await runParameterizedQuery(
            db,
            "changed_projects",
          )) as ProjectSummary[],
          artifacts: {
            summary: summaries,
            status: {
              blockchain: (await runParameterizedQuery(
                db,
                "changed_blockchain_artifacts",
              )) as BlockchainStatus[],
              url: (await runParameterizedQuery(
                db,
                "changed_url_artifacts",
              )) as UrlStatus[],
            },
            toValidate: {
              blockchain: (await runParameterizedQuery(
                db,
                "changed_blockchain_artifacts_to_validate",
              )) as BlockchainValidationItem[],
              defillama: (await runParameterizedQuery(
                db,
                "changed_defillama_artifacts_to_validate",
              )) as UrlItem[],
            },
          },
        };
        this.changes = changes;

        // For simple debugging purposes we provide a REPL to explore the data.
        if (args.repl) {
          console.log("\nTry a query like this:");
          console.log(
            "  $db.$('SELECT DISTINCT COUNT(address) FROM pr_blockchain_artifacts')",
          );
          const server = repl.start("> ");
          server.context.$db = {
            // Setup raw access to the duckdb api via db
            raw: db,
            // Setup a convenience command that runs queries
            $: async (query: string) => {
              await this.runQuery(query);
            },
            $$: async (query: string) => {
              return await this.runQuery(query, true);
            },
            runQuery: async (query: string) => {
              return await this.runQuery(query, true);
            },
            runParameterizedQuery: async (
              name: string,
              params?: Record<string, unknown>,
            ) => {
              return await this.runParameterizedQuery(name, params);
            },
          };
          server.context.changes = this.changes;
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
    const args = this.args;

    const unchangedProjects = (await this.runParameterizedQuery(
      "unchanged_projects",
    )) as {
      total: number;
    }[];

    const unchangedProjectsCount =
      unchangedProjects.length === 0 ? 0 : unchangedProjects.length;
    const updatedProjectsCount = this.changes.projects.length;

    await args.appUtils.setStatusComment(
      args.pr,
      await renderMustacheFromFile(relativeDir("messages", "list-changes.md"), {
        projects: {
          added: updatedProjectsCount,
          removed: 0,
          unchanged: unchangedProjectsCount,
        },
        artifacts: this.changes.artifacts.summary,
        sha: args.sha,
      }),
      "external-pr-changes-list",
    );
  }

  async validate(urls: RpcUrlArgs) {
    const args = this.args;
    logger.info({
      message: "validating the pull request",
      repo: args.repo,
      sha: args.sha,
      pr: args.pr,
    });
    // Initialize
    await this.loadValidators(urls);
    const results = await ValidationResults.create();

    // Validate blockchain artifacts
    const addressesToValidate =
      this.changes.artifacts.toValidate.blockchain.map((b) => b.address);
    logger.info({
      message: `Starting blockchain validations for [${addressesToValidate}]. ${addressesToValidate.length} total`,
      addresses: addressesToValidate,
    });

    for (const item of this.changes.artifacts.toValidate.blockchain) {
      const address = item.address;
      for (const network of item.networks) {
        const validator =
          this.blockchainValidators[uncheckedCast<BlockchainNetwork>(network)];
        if (!validator) {
          results.addWarning(
            `no automated validators exist on ${network} to check tags=[${item.tags}]. Please check manually.`,
            address,
            { network },
          );
          //throw new Error(`No validator found for network "${network}"`);
          continue;
        }

        logger.info({
          message: `validating address ${address} on ${network} for [${item.tags}]`,
          address: address,
          network: network,
          tags: item.tags,
        });

        for (const rawTag of item.tags) {
          const tag = uncheckedCast<BlockchainTag>(rawTag);
          const genericChecker = async (fn: () => Promise<boolean>) => {
            if (!(await fn())) {
              results.addError(
                `${address} is not a ${tag} on ${network}`,
                address,
                { address, tag, network },
              );
            } else {
              results.addSuccess(
                `${address} is a '${tag}' on ${network}`,
                address,
                { address, tag, network },
              );
            }
          };
          if (tag === "eoa") {
            await genericChecker(() => validator.isEOA(address));
          } else if (tag === "contract") {
            if (network === "any_evm") {
              results.addWarning(
                `addresses with the 'contract' tag should enumerate all networks that it is deployed on, rather than use 'any_evm'`,
                address,
                { address, tag, network },
              );
            } else {
              await genericChecker(() => validator.isContract(address));
            }
          } else if (tag === "deployer") {
            await genericChecker(() => validator.isDeployer(address));
          } else {
            results.addWarning(
              `missing validator for ${tag} on ${network}`,
              address,
              { tag, network },
            );
          }
        }
      }
    }

    // DefiLlama validations
    const defillamaToValidate = this.changes.artifacts.toValidate.defillama.map(
      (x) => x.url_value,
    );
    logger.info({
      message: `Starting DefiLlama validations for [${defillamaToValidate}]. ${defillamaToValidate.length} total`,
      addresses: defillamaToValidate,
    });

    for (const item of this.changes.artifacts.toValidate.defillama) {
      console.log(item);
      const urlValue = item.url_value;
      const urlType = item.url_type;
      logger.info({
        message: `validating DefiLlama ${urlValue}`,
        url: urlValue,
        type: urlType,
      });
      if (!this.defillamaValidator.isValidUrl(urlValue)) {
        results.addError(
          `${urlValue} is not a valid DefiLlama URL`,
          urlValue,
          item,
        );
      } else {
        results.addSuccess(
          `${urlValue} is a valid DefiLlama URL`,
          urlValue,
          item,
        );
      }
      if (!(await this.defillamaValidator.isValid(urlValue))) {
        results.addError(
          `${urlValue} is not a valid DefiLlama slug`,
          urlValue,
          item,
        );
      } else {
        results.addSuccess(
          `${urlValue} is a valid DefiLlama slug`,
          urlValue,
          item,
        );
      }
    }

    // Render the results to GitHub PR
    const { numErrors, summaryMessage, commentBody } = await results.render(
      args.sha,
    );
    // Update the PR comment
    await args.appUtils.setStatusComment(args.pr, commentBody);
    // Update the PR status
    await args.appUtils.setCheckStatus({
      conclusion:
        numErrors > 0 ? CheckConclusion.Failure : CheckConclusion.Success,
      name: "validate",
      head_sha: args.sha,
      status: CheckStatus.Completed,
      output: {
        title:
          numErrors > 0 ? summaryMessage : "Successfully validated all items",
        summary: commentBody,
      },
    });
  }
}

async function listPR(args: OSSDirectoryPullRequestArgs) {
  const pr = await OSSDirectoryPullRequest.init(args);
  await pr.list();
}

async function validatePR(args: ValidatePRArgs) {
  const pr = await OSSDirectoryPullRequest.init(args);
  await pr.validate(args);
}

/**
 * This command is called by external-prs-handle-comment as a check
 * for whether we should run the validation logic,
 * based on whether a valid command was called.
 **/
async function parseOSSDirectoryComments(args: ParseCommentArgs) {
  const enableValidation: CommmentCommandHandler<GithubOutput> = async (
    command,
  ) => {
    if (command.args.splitArgs.length < 1) {
      throw new Error("sha required for validation");
    }
    const sha = command.args.splitArgs[0];

    if (command.user.login === "") {
      throw new Error("validation command requires a user");
    }

    if (["admin", "write"].indexOf(command.user.permissions || "") === -1) {
      throw new Error("user not allowed to enable validation");
    }

    return new GithubOutput({
      sha: sha,
      deploy: "true",
      pr: command.issue.id,
      issueAuthor: command.issue.author,
      commentAuthor: command.comment.author,
    });
  };

  const commandHandlers = {
    // /validate <sha>
    validate: enableValidation,
  };

  try {
    const output = await args.appUtils.parseCommentForCommand<GithubOutput>(
      args.comment,
      commandHandlers,
    );
    await output.commit(args.output);
  } catch (e) {
    logger.debug("Error", e);
    await GithubOutput.write(args.output, {
      deploy: "false",
    });
  }
}
