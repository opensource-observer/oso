import yargs from "yargs";
import { ArgumentsCamelCase } from "yargs";
import { hideBin } from "yargs/helpers";
import { App, Octokit } from "octokit";

import { logger } from "./logger.js";
import { handleError } from "./error.js";
import dotenv from "dotenv";
import { Repo, getOctokitFor } from "./app.js";
import { CheckStatus, setCheckStatus, CheckConclusion } from "./checks.js";

dotenv.config();

interface BaseArgs {
  githubAppPrivateKey: string;
  githubAppId: string;
  repo: Repo;
  app: App;
}

type BeforeClientArgs = ArgumentsCamelCase<{
  "github-app-private-key": unknown;
  "github-app-id": unknown;
}>;

interface InitializePRCheck extends BaseArgs {
  sha: string;
  login: string;
  checkName: string;
}

async function getRepoPermissions(octo: Octokit, repo: Repo, login: string) {
  const res = await octo.rest.repos.getCollaboratorPermissionLevel({
    owner: repo.owner,
    repo: repo.name,
    username: login,
  });
  return res.data.permission;
}

async function initializePrCheck(args: InitializePRCheck) {
  logger.info({
    message: "initializing an admin only PR check",
    repo: args.repo,
    sha: args.sha,
    login: args.login,
    checkName: args.checkName,
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
      name: "test-deploy",
      head_sha: args.sha,
      status: CheckStatus.Completed,
      conclusion: CheckConclusion.ActionRequired,
      output: {
        title: "Deployment approval required to deploy",
        summary:
          "Deployment pproval required to deploy. A valid user must comment `/test-deploy ${sha}` on the PR.",
      },
    });
  }
}

export function appCli() {
  const cli = yargs(hideBin(process.argv))
    .positional("repo", {
      type: "string",
      description: "The repo in the style owner/repo_name",
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

      const { data } = await app.octokit.request("/app");
      logger.debug(`Authenticated as ${data.name}`);
    })
    .command<InitializePRCheck>(
      "initialize-check <repo> <sha> <login> <check-name>",
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
          description: "The name for the check to initialize",
        });
      },
      (args) => handleError(initializePrCheck(args)),
    )
    .demandCommand()
    .strict()
    .help("h")
    .alias("h", "help");
  return cli;
}
