import { Repo, getOctokitFor, getRepoPermissions } from "./app.js";
import { logger } from "./logger.js";
import { App } from "octokit";
import { NoRepoError } from "./error.js";

export interface CommentCommand {
  repo: Repo;
  commentId: number;
  user: {
    login?: string | null;
    permissions?: string | null;
  };
  command: string;
  body: string;
}

export class NoUserError extends Error {}

export class NoCommandError extends Error {}

export async function parseCommentForCommand(
  app: App,
  repo: Repo,
  commentId: number,
): Promise<CommentCommand> {
  logger.info({
    message: "checking for a /deploy-test message",
    repo: repo,
    commentId: commentId,
  });

  const octo = await getOctokitFor(app, repo);
  if (!octo) {
    throw new NoRepoError("No repo found");
  }

  const comment = await octo.rest.issues.getComment({
    repo: repo.name,
    owner: repo.owner,
    comment_id: commentId,
  });
  logger.info("gathered the comment", {
    commentId: comment.data.id,
    authorAssosication: comment.data.author_association,
    author: comment.data.user?.login,
  });

  const login = comment.data.user?.login;
  let permissions: string | null = null;
  if (login) {
    // Get the author's permissions
    permissions = await getRepoPermissions(octo, repo, login);

    logger.info({
      message: "gathered the commentor's permissions",
      login: login,
      permissions: permissions,
    });
  }

  const body = comment.data.body || "";
  const match = body.match(/^\/([a-z-]+)\s+(.*)$/);
  if (!match) {
    logger.error("command not found");
    throw new NoCommandError("No command error");
  }
  if (match.length < 2) {
    logger.error({
      message: "proper command not found",
      matches: match,
    });
    throw new NoCommandError("No command error");
  }

  return {
    repo: repo,
    commentId: commentId,
    body: comment.data.body || "",
    user: {
      login: login,
      permissions: permissions,
    },
    command: match[1],
  };
}
