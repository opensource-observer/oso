import yargs from "yargs";
import { Argv, ArgumentsCamelCase } from "yargs";
import { hideBin } from "yargs/helpers";
import { App, Octokit } from "octokit";
import * as fsPromise from "fs/promises";
import _sodium from "libsodium-wrappers";
import { BigQuery } from "@google-cloud/bigquery";
import { dedent } from "ts-dedent";
import { URL } from "url";

import { logger } from "./utils/logger.js";
import { handleError } from "./utils/error.js";
import dotenv from "dotenv";
import { CheckStatus, setCheckStatus, CheckConclusion } from "./checks.js";
import { Repo, getOctokitFor } from "./github.js";
import { PRTestDeployCoordinator } from "./deploy.js";

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

interface ParseCommentArgs extends BaseArgs {
  comment: number;
  output: string;
}

interface InitializePRCheck extends BaseArgs {
  sha: string;
  login: string;
}

interface RefreshGCPCredentials extends BaseArgs {
  environment: string;
  credsPath: string;
  secret: boolean;
  name: string;
}

interface TestDeployArgs extends BaseArgs {
  coordinator: PRTestDeployCoordinator;
}

interface TestDeploySetupArgs extends TestDeployArgs {
  pr: number;
  sha: number;
  profilePath: string;
  serviceAccountPath: string;
  projectId: string;
}

interface TestDeployPeriodicCleaningArgs extends TestDeployArgs {
  ttlSeconds: number;
}

interface TestDeployTeardownArgs extends TestDeployArgs {
  pr: number;
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

  const permissions = await octo.rest.repos.getCollaboratorPermissionLevel({
    owner: args.repo.owner,
    repo: args.repo.name,
    username: args.login,
  });

  // If this user has write then we can show this as being queued
  if (["admin", "write"].indexOf(permissions.data.permission) !== -1) {
    await setCheckStatus(octo, args.repo.owner, args.repo.name, {
      name: "test-deploy",
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

async function parseDeployComment(args: ParseCommentArgs) {
  logger.info({
    message: "checking for a /deploy-test message",
    repo: args.repo,
    commentId: args.comment,
  });

  const app = args.app;

  const octo = await getOctokitFor(app, args.repo);
  if (!octo) {
    throw new Error("No repo found");
  }

  const noDeploy = async () => {
    const output = dedent`
    deploy=false
    `;

    // Write the deploy commit sha to the
    await fsPromise.writeFile(args.output, output);
  };

  const comment = await octo.rest.issues.getComment({
    repo: args.repo.name,
    owner: args.repo.owner,
    comment_id: args.comment,
  });
  if (
    ["OWNER", "COLLABORATOR", "MEMBER"].indexOf(
      comment.data.author_association,
    ) === -1
  ) {
    return await noDeploy();
  }
  const body = comment.data.body || "";
  const match = body.match(/\/deploy-test\s+([0-9a-f]{6,40})/);
  if (!match) {
    return await noDeploy();
  }

  const issueUrl = comment.data.issue_url;
  const url = new URL(issueUrl);
  const issueNumber = parseInt(url.pathname.split("/").slice(-1)[0]);

  const sha = match[1];

  const issue = await octo.rest.issues.get({
    issue_number: issueNumber,
    repo: args.repo.name,
    owner: args.repo.owner,
  });

  // Output for GITHUB_OUTPUT for now.
  const output = dedent`
  deploy=true
  sha=${sha}
  pr=${issueNumber}
  issue_author=${issue.data.user?.login}
  comment_author=${comment.data.user?.login}
  `;

  // Write the deploy commit sha to the
  await fsPromise.writeFile(args.output, output);

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

async function fileToBase64(filePath: string): Promise<string> {
  try {
    const fileBuffer = await fsPromise.readFile(filePath);
    const base64String = fileBuffer.toString("base64");
    return base64String;
  } catch (error) {
    logger.error("Error reading file:", error);
    throw error;
  }
}

async function refreshCredentials(args: RefreshGCPCredentials) {
  logger.info({
    message: "setting up credentials",
    environment: args.environment,
    name: args.name,
  });

  const app = args.app;

  const octo = await getOctokitFor(app, args.repo);
  if (!octo) {
    throw new Error("No repo found");
  }

  const repo = await octo.rest.repos.get({
    repo: args.repo.name,
    owner: args.repo.owner,
  });

  const creds = await fileToBase64(args.credsPath);

  if (args.secret) {
    // The github secret must use libsodium's crypto_box_seal for the
    // `encrypted_value`
    await _sodium.ready;

    const pkey = await octo.rest.actions.getEnvironmentPublicKey({
      repository_id: repo.data.id,
      environment_name: args.environment,
    });

    const messageBytes = Buffer.from(creds);
    const keyBytes = Buffer.from(pkey.data.key, "base64");
    const encryptedBytes = _sodium.crypto_box_seal(messageBytes, keyBytes);
    const ciphertext = Buffer.from(encryptedBytes).toString("base64");

    await octo.rest.actions.createOrUpdateEnvironmentSecret({
      repository_id: repo.data.id,
      environment_name: args.environment,
      secret_name: args.name,
      encrypted_value: ciphertext,
      key_id: pkey.data.key_id,
    });
  } else {
    try {
      const currentVar = await octo.rest.actions.getEnvironmentVariable({
        repository_id: repo.data.id,
        environment_name: args.environment,
        name: args.name,
      });
      if (currentVar) {
        await octo.rest.actions.deleteEnvironmentVariable({
          repository_id: repo.data.id,
          environment_name: args.environment,
          name: args.name,
        });
      }
    } catch (e) {
      logger.info("no existing var found");
    }
    await octo.rest.actions.createEnvironmentVariable({
      repository_id: repo.data.id,
      environment_name: args.environment,
      name: args.name,
      value: creds,
    });
  }
}

async function testDeploySetup(args: TestDeploySetupArgs) {
  return args.coordinator.setup(
    args.pr,
    args.profilePath,
    args.serviceAccountPath,
    args.sha,
  );
}

async function testDeployTeardown(args: TestDeployTeardownArgs) {
  return args.coordinator.teardown(args.pr);
}

async function testDeployPeriodicCleaning(
  args: TestDeployPeriodicCleaningArgs,
) {
  return args.coordinator.clean(args.ttlSeconds);
}

function testDeployGroup(group: Argv) {
  group
    .option("project-id", {
      description: "The google project id to deploy into",
      type: "string",
      demandOption: true,
    })
    .middleware(async (args: ArgumentsCamelCase) => {
      logger.info({
        message: "settings up Pull Request Test Deploy Coordinator",
      });

      const bq = new BigQuery();
      const app = args.app as App;
      const repo = args.repo as Repo;

      const octo = await getOctokitFor(app, repo);

      args.coordinator = new PRTestDeployCoordinator(
        repo,
        app,
        octo as Octokit,
        bq,
        args.projectId as string,
      );
    })
    .command<TestDeploySetupArgs>(
      "setup <repo> <pr> <profile-path> <service-account-path>",
      "subcommand for a setting up a test deployment",
      (yags) => {
        yags.positional("pr", {
          description: "The PR",
        });
        yags.positional("profile-path", {
          description: "the profile path to write to",
        });
        yags.positional("service-account-path", {
          description: "the profile path to write to",
        });
      },
      (args) => handleError(testDeploySetup(args)),
    )
    .command<TestDeployTeardownArgs>(
      "teardown <repo> <pr>",
      "subcommand for a setting up a test deployment",
      (yags) => {
        yags.positional("pr", {
          description: "The PR",
        });
      },
      (args) => handleError(testDeployTeardown(args)),
    )
    .command<TestDeployPeriodicCleaningArgs>(
      "clean <repo> <ttl-seconds>",
      "subcommand for cleaning test deployments",
      (yags) => {
        yags.positional("pr", {
          description: "The PR",
        });
        yags.positional("ttl-seconds", {
          type: "number",
          description: "TTL in seconds. Defaults to 1209600",
          default: 1_209_600,
        });
      },
      (args) => handleError(testDeployPeriodicCleaning(args)),
    )
    .demandCommand();
}

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
    "initialize-check <repo> <sha> <login>",
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
  .command<RefreshGCPCredentials>(
    "refresh-gcp-credentials <repo> <environment> <creds-path> <name>",
    "Refresh creds",
    (yags) => {
      yags.positional("environment", {
        type: "string",
      });
      yags.positional("creds-path", {
        type: "string",
      });
      yags.positional("name", {
        type: "string",
      });
      yags.option("secret", {
        type: "boolean",
        default: true,
      });
      yags.boolean("secret");
    },
    (args) => handleError(refreshCredentials(args)),
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
