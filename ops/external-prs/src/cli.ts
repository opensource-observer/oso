import yargs from "yargs";
import { Argv, ArgumentsCamelCase } from "yargs";
import { hideBin } from "yargs/helpers";
import { App, Octokit } from "octokit";
import * as fsPromise from "fs/promises";

import { logger } from "./utils/logger.js";
import { handleError } from "./utils/error.js";
import dotenv from "dotenv";
import { CheckStatus, setCheckStatus } from "./checks.js";

dotenv.config();

//const callLibrary = async <Args>(
//  func: EventSourceFunction<Args>,
//  args: Args,
//): Promise<void> => {
// TODO: handle ApiReturnType properly and generically here
//  const result = await func(args);
//  console.log(result);
//};

// function outputError(err: unknown) {
//   logger.info(err);
//   try {
//     logger.error(JSON.stringify(err));
//     // eslint-disable-next-line no-restricted-properties
//     console.error(err);
//   } catch (_e) {
//     logger.error("Cannot stringify error.");
//     logger.error(err);
//     // eslint-disable-next-line no-restricted-properties
//     console.error(err);
//   }
// }

interface Repo {
  name: string;
  owner: string;
}

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

interface ParseCommentArgs extends BaseArgs {
  comment: number;
  output: string;
}

interface InitializePRCheck extends BaseArgs {
  sha: string;
}

interface TestDeployArgs extends BaseArgs {}

interface TestDeploySetupArgs extends TestDeployArgs {}

interface TestDeployTeardownArgs extends TestDeployArgs {}

async function getOctokitFor(app: App, repo: Repo): Promise<Octokit | void> {
  for await (const { installation } of app.eachInstallation.iterator()) {
    for await (const { octokit, repository } of app.eachRepository.iterator({
      installationId: installation.id,
    })) {
      if (repository.full_name === `${repo.owner}/${repo.name}`) {
        return octokit;
      }
    }
  }
  return;
}

async function initializePrCheck(args: InitializePRCheck) {
  logger.info({
    message: 'initializing the PR check to "queued"',
    repo: args.repo,
    sha: args.sha,
  });

  const app = args.app;
  const octo = await getOctokitFor(app, args.repo);
  if (!octo) {
    throw new Error("No repo found");
  }

  await setCheckStatus(octo, args.repo.owner, args.repo.name, {
    name: "test-deploy",
    head_sha: args.sha,
    status: CheckStatus.Queued,
    output: {
      title: "Test Deployment",
      summary: "Queued for deployment",
    },
  });
}

async function parseDeployComment(args: ParseCommentArgs) {
  logger.info({
    message: "checking for a /deploy message",
    repo: args.repo,
    commentId: args.comment,
  });

  const app = args.app;

  const octo = await getOctokitFor(app, args.repo);
  if (!octo) {
    throw new Error("No repo found");
  }

  const comment = await octo.rest.issues.getComment({
    repo: args.repo.name,
    owner: args.repo.owner,
    comment_id: args.comment,
  });
  const body = comment.data.body || "";
  const match = body.match(/\/deploy\s+([0-9a-f]{6,40})/);
  if (!match) {
    process.exit(1);
  }

  const sha = match[1];

  // Write the deploy commit sha to the
  await fsPromise.writeFile(args.output, match[1]);

  // Update the check for this PR
  await setCheckStatus(octo, args.repo.owner, args.repo.name, {
    name: "test-deploy",
    head_sha: sha,
    status: CheckStatus.Queued,
    output: {
      title: "Test Deployment",
      summary: "Queued for deployment",
    },
  });
}

async function testDeploySetup(_args: TestDeployArgs) {
  console.log("setup");
  // This should create a new public dataset inside a "testing" project
  // specifically for a pull request
  //
  // This project is intended to be only used to push the last 2 days worth of
  // data into a dev environment
  //
  // The service account associated with this account should only have access to
  // bigquery no other resources. The service account should also continously be
  // rotated. So the project in use should have a very short TTL on service
  // account keys.
}

async function testDeployTeardown(_args: TestDeployArgs) {
  console.log("teardown");
  // This will delete a pull request
}

function testDeployGroup(group: Argv) {
  group
    .option("project-id", {
      description: "The google project id to deploy into",
      type: "string",
      demandOption: true,
    })
    .command<TestDeploySetupArgs>(
      "setup <repo> <pr>",
      "subcommand for a setting up a test deployment",
      (yags) => {
        yags.positional("pr", {
          description: "The PR",
        });
      },
      (args) => handleError(testDeploySetup(args)),
    )
    .command<TestDeployTeardownArgs>(
      "teardown <repo> <pr>",
      "subcommand for a setting up a test deployment",
      (_yags) => {},
      (args) => handleError(testDeployTeardown(args)),
    )
    .demandCommand();
}

/**
 * When adding a new fetcher, please remember to add it to both this registry and yargs
 */
export const FETCHER_REGISTRY = [
  //NpmDownloadsInterface,
];
const cli = yargs(hideBin(process.argv))
  .env("PR_TOOLS")
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
    "initialize-check <repo> <sha>",
    "subcommand for initializing a check",
    (yags) => {
      yags.positional("sha", {
        type: "string",
        description: "The sha for the check to initialize",
      });
    },
    (args) => handleError(initializePrCheck(args)),
  )
  .command<ParseCommentArgs>(
    "parse-comment <repo> <comment> <output>",
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
    (args) => handleError(parseDeployComment(args)),
  )
  .command<TestDeployArgs>(
    "test-deploy",
    "Test deployment commands",
    (yags) => {
      testDeployGroup(yags);
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
