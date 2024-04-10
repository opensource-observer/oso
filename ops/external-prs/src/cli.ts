import yargs from "yargs";
import { ArgumentsCamelCase } from "yargs";
import { hideBin } from "yargs/helpers";
import { App } from "octokit";

import { logger } from "./utils/logger.js";
import { handleError } from "./utils/error.js";
import dotenv from "dotenv";
import { CheckStatus, setCheckStatus, CheckConclusion } from "./checks.js";
import { Repo, getOctokitFor, getRepoPermissions } from "./github.js";
import { osoSubcommands } from "./oso/index.js";
import { BaseArgs, GHAppUtils } from "./base.js";
import { ossdSubcommands } from "./ossd/index.js";

dotenv.config();

type BeforeClientArgs = ArgumentsCamelCase<{
  "github-app-private-key": unknown;
  "github-app-id": unknown;
}>;

interface InitializePRCheck extends BaseArgs {
  sha: string;
  login: string;
  checkName: string;
}

async function initializePrCheck(args: InitializePRCheck) {
  logger.info({
    message: "initializing the PR check",
    repo: args.repo,
    sha: args.sha,
    login: args.login,
  });

  const app = args.app;
  const octo = await getOctokitFor(app, args.repo);
  if (!octo) {
    throw new Error("No repo found");
  }

  const permissions = await getRepoPermissions(octo, args.repo, args.login);

  // If this user has write then we can show this as being queued
  if (["admin", "write"].indexOf(permissions) !== -1) {
    await setCheckStatus(octo, args.repo.owner, args.repo.name, {
      name: args.checkName,
      head_sha: args.sha,
      status: CheckStatus.Queued,
      output: {
        title: "Test deployment queued",
        summary: "Test deployment queued",
      },
    });
  } else {
    // The user is not a writer. Show that this needs to be approved.
    await setCheckStatus(octo, args.repo.owner, args.repo.name, {
      name: args.checkName,
      head_sha: args.sha,
      status: CheckStatus.Completed,
      conclusion: CheckConclusion.ActionRequired,
      output: {
        title: `Approval required for ${args.checkName}`,
        summary: `Approval required for the ${args.checkName} check.`,
      },
    });
  }
}

const cli = yargs(hideBin(process.argv))
  .env("PR_TOOLS")
  .option("repo", {
    type: "string",
    description: "The repo in the style owner/repo_name",
    demandOption: true,
  })
  .coerce("repo", (v: string): Repo => {
    const splitName = v.split("/");
    if (splitName.length !== 2) {
      throw new Error("Repo name must be an owner/repo_name pair");
    }
    return {
      owner: splitName[0],
      name: splitName[1],
    };
  })
  .option("github-app-private-key", {
    description: "The private key for the github app",
    type: "string",
    demandOption: true,
  })
  .option("github-app-id", {
    description: "The private key for the github app",
    type: "string",
    demandOption: true,
  })
  .middleware(async (args: BeforeClientArgs) => {
    const buf = Buffer.from(args.githubAppPrivateKey as string, "base64"); // Ta-da

    const app = new App({
      appId: args.githubAppId as string,
      privateKey: buf.toString("utf-8"),
    });
    args.app = app;
    const repo = args.repo as Repo;
    const octo = await getOctokitFor(app, repo);
    args.appUtils = new GHAppUtils(app, repo, octo);

    const { data } = await app.octokit.request("/app");
    logger.debug(`Authenticated as ${data.name}`);
  })
  .command("oso", "oso related commands", (yags) => {
    osoSubcommands(yags);
  })
  .command("ossd", "oss-directory related commands", (yags) => {
    ossdSubcommands(yags);
  })
  .command<InitializePRCheck>(
    "initialize-check <sha> <login> <check-name>",
    "subcommand for initializing a check",
    (yags) => {
      yags.positional("sha", {
        type: "string",
        description: "The sha for the check to initialize",
      });
      yags.positional("login", {
        type: "string",
        description: "The login for the PR",
      });
      yags.positional("check-name", {
        type: "string",
        description: "The check-name to use",
      });
    },
    (args) => handleError(initializePrCheck(args)),
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
