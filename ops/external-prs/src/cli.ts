import yargs from "yargs";
import { Argv, ArgumentsCamelCase } from "yargs";
import { hideBin } from "yargs/helpers";
import { App, Octokit } from "octokit";

import { logger } from "./utils/logger.js";
import { handleError } from "./utils/error.js";
import dotenv from "dotenv";

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

interface BaseArgs {
  githubAppPrivateKey: string;
  githubAppId: string;
  app: App;
}

type BeforeClientArgs = ArgumentsCamelCase<{
  "github-app-private-key": unknown;
  "github-app-id": unknown;
}>;

interface CheckArgs extends BaseArgs {
  owner: string;
  repo: string;
}

interface CommentCheckArgs extends CheckArgs {
  comment: number;
}

interface PRCheckArgs extends CheckArgs {
  pr: number;
}

interface TestDeployArgs extends BaseArgs {}

interface TestDeploySetupArgs extends TestDeployArgs {}

interface TestDeployTeardownArgs extends TestDeployArgs {}

async function getOctokitFor(
  app: App,
  owner: string,
  repo: string,
): Promise<Octokit | void> {
  for await (const { installation } of app.eachInstallation.iterator()) {
    for await (const { octokit, repository } of app.eachRepository.iterator({
      installationId: installation.id,
    })) {
      if (repository.full_name === `${owner}/${repo}`) {
        return octokit;
      }
    }
  }
  return;
}

async function commentCheck(args: CommentCheckArgs) {
  //console.log('comment');

  const app = args.app;

  const octo = await getOctokitFor(app, args.owner, args.repo);
  if (!octo) {
    throw new Error("No repo found");
  }

  const comment = await octo.rest.issues.getComment({
    repo: args.repo,
    owner: args.owner,
    comment_id: args.comment,
  });
  const body = comment.data.body || "";
  const match = body.match(/\/deploy\s+([0-9a-f]{6,40})/);
  if (!match) {
    process.exit(1);
  }

  console.log(match[0]);
}

async function prCheck(_args: PRCheckArgs) {
  console.log("pr");
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

function checkCommandGroup(group: Argv) {
  group.command<CommentCheckArgs>(
    "comment <owner> <repo> <comment>",
    "subcommand for comment check",
    (yags) => {
      yags.positional("comment", {
        type: "number",
        description: "Comment ID",
      });
    },
    (args) => handleError(commentCheck(args)),
  );
  group.command<PRCheckArgs>(
    "pr <owner> <repo> <pr>",
    "subcommand for PR check",
    (yags) => {
      yags.positional("pr", {
        type: "number",
        description: "Pull Request ID",
      });
    },
    (args) => handleError(prCheck(args)),
  );
  group.demandCommand();
}

function testDeployGroup(group: Argv) {
  group.command<TestDeploySetupArgs>(
    "setup",
    "subcommand for a setting up a test deployment",
    (_yags) => {},
    (args) => handleError(testDeploySetup(args)),
  );
  group.command<TestDeployTeardownArgs>(
    "teardown",
    "subcommand for a setting up a test deployment",
    (_yags) => {},
    (args) => handleError(testDeployTeardown(args)),
  );
  group.demandCommand();
}

/**
 * When adding a new fetcher, please remember to add it to both this registry and yargs
 */
export const FETCHER_REGISTRY = [
  //NpmDownloadsInterface,
];
const cli = yargs(hideBin(process.argv))
  .env("PR_TOOLS")
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
  .command<CheckArgs>("check", "Github Check related commands", (yags) => {
    checkCommandGroup(yags);
  })
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
