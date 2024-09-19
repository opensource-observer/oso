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
import { commonSubcommands } from "./common/index.js";

dotenv.config();

type BeforeClientArgs = ArgumentsCamelCase<{
  "github-app-private-key": unknown;
  "github-app-id": unknown;
  "admin-team-name": string;
}>;

interface InitializePRCheck extends BaseArgs {
  // Commit SHA
  sha: string;
  // GitHub user
  login: string;
  checkName: string;
}

/**
 * Checks if the user has write access.
 * If yes, we signal that we've already queued a job.
 * Otherwise, signal that we need admin approval.
 * This is typically run with the initiator of the pull request
 **/
async function initializePrCheck(args: InitializePRCheck) {
  logger.info({
    message: "initializing the PR check",
    repo: args.repo,
    sha: args.sha,
    login: args.login,
  });

  const app = args.app;
  const octokitAndAppMeta = await getOctokitFor(app, args.repo);
  const octo = octokitAndAppMeta.octo;
  if (!octokitAndAppMeta) {
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
        title: "Test workflow has been queued",
        summary:
          "Test workflow has been queued. Please check the corresponding owners workflow for the latest job status.",
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
        summary: `Approval required for the ${args.checkName} check. Repo admins can run '/${args.checkName} LATEST_COMMIT_SHA'. Remember to use the latest commit SHA, or validation will fail.`,
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
  .option("admin-team-name", {
    description: "The admin team within the repo's organization",
    type: "string",
    default: "",
    demandOption: false,
  })
  .middleware(async (args: BeforeClientArgs) => {
    // Get base64-encoded private key from the environment
    const buf = Buffer.from(args.githubAppPrivateKey as string, "base64"); // Ta-da
    // Log into GitHub Octokit
    const app = new App({
      appId: args.githubAppId as string,
      privateKey: buf.toString("utf-8"),
    });
    args.app = app;
    const repo = args.repo as Repo;
    const octokitAndAppMeta = await getOctokitFor(app, repo);
    args.appUtils = new GHAppUtils(
      app,
      repo,
      args.adminTeamName,
      octokitAndAppMeta,
    );

    const { data } = await app.octokit.request("/app");
    logger.debug(`Authenticated as ${data.name}`);
  })
  .command("common", "common commands", (yags) => {
    commonSubcommands(yags);
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
