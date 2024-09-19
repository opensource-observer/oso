import { Argv } from "yargs";

import { logger } from "../utils/logger.js";
import { handleError } from "../utils/error.js";
import { getOctokitFor } from "../github.js";
import { BaseArgs } from "../base.js";
import * as fsPromise from "fs/promises";

interface AttemptAutoApproveArgs extends BaseArgs {
  pr: number;
}

interface IsRepoAdminArgs extends BaseArgs {
  login: string;
  outputFile: string;
}

export function commonSubcommands(yargs: Argv) {
  yargs
    .command<AttemptAutoApproveArgs>(
      "attempt-auto-approve <pr>",
      "Attempts to auto approve a PR",
      (yags) => {
        yags.positional("pr", {
          type: "string",
          description: "The pr number",
        });
      },
      (args) => handleError(attemptAutoApprove(args)),
    )
    .command<IsRepoAdminArgs>(
      "is-repo-admin <login>",
      "checks if the current user is the repo admin",
      (yags) => {
        yags.positional("login", {
          type: "string",
          description: "The login to check for admin status",
        });
        yags.option("output-file", {
          type: "string",
          description: "optional output file",
        });
      },
      (args) => handleError(isRepoAdmin(args)),
    )
    .demandCommand();
}

async function isRepoAdmin(args: IsRepoAdminArgs) {
  if (!(await args.appUtils.isLoginOnAdminTeam(args.login))) {
    if (args.outputFile) {
      await fsPromise.appendFile(args.outputFile, "is_admin=0\nteam=none");
    }
    logger.info("user is not admin");
  } else {
    if (args.outputFile) {
      await fsPromise.appendFile(args.outputFile, "is_admin=1\nteam=admin");
    }
    logger.info("user is an admin");
  }
}

async function attemptAutoApprove(args: AttemptAutoApproveArgs) {
  logger.info({
    message: "loading the pr",
    pr: args.pr,
  });

  const app = args.app;
  const { octo } = await getOctokitFor(app, args.repo);
  if (!octo) {
    throw new Error("No repo found");
  }

  const pr = await octo.rest.pulls.get({
    repo: args.repo.name,
    owner: args.repo.owner,
    pull_number: args.pr,
  });

  // check if the PR is already approved. If so, do nothing
  const currentReviews = await octo.rest.pulls.listReviews({
    repo: args.repo.name,
    owner: args.repo.owner,
    pull_number: args.pr,
  });

  const approvedReviews = currentReviews.data.filter(
    (review) => review.state == "APPROVED",
  );
  if (approvedReviews.length > 0) {
    logger.info("pr already approved");
    return;
  }

  const login = pr.data.user.login;

  if (!(await args.appUtils.isLoginOnAdminTeam(login))) {
    logger.info({ message: "creator is not an admin", creator: login });
    return;
  }
  logger.info({ message: "approving the pr" });

  await octo.rest.pulls.createReview({
    owner: args.repo.owner,
    repo: args.repo.name,
    pull_number: args.pr,
    event: "APPROVE",
    body: "Auto-approved! please merge responsibly :smile:",
  });
}
