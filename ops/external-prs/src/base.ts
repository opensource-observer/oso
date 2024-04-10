import { CheckRequest, setCheckStatus } from "./checks.js";
import { Repo, getRepoPermissions } from "./github.js";
import { App, Octokit } from "octokit";
import { logger } from "./utils/logger.js";
import { URL } from "url";

export interface BaseArgs {
  githubAppPrivateKey: string;
  githubAppId: string;
  repo: Repo;
  app: App;
  appUtils: GHAppUtils;
}

export interface CommentCommand {
  repo: Repo;
  comment: {
    id: number;
    author: string;
  };
  issue: {
    id: number;
    author: string;
  };
  user: {
    login: string;
    permissions: string;
  };
  command: string;
  body: string;
  args: {
    raw: string;
    splitArgs: string[];
  };
}

export class NoUserError extends Error {}

export class NoCommandError extends Error {}

export type CommmentCommandHandler<T> = (command: CommentCommand) => Promise<T>;

/**
 * Convenience utilities for external PRs
 */
export class GHAppUtils {
  private app: App;
  private repo: Repo;
  private octo: Octokit;

  constructor(app: App, repo: Repo, octo: Octokit) {
    this.app = app;
    this.repo = repo;
    this.octo = octo;
  }

  async leaveCommentOnPr(pr: number, comment: string) {
    await this.octo.rest.issues.createComment({
      owner: this.repo.owner,
      repo: this.repo.name,
      body: comment,
      issue_number: pr,
    });
  }

  async setCheckStatus(checkName: string, request: CheckRequest) {
    return setCheckStatus(this.octo, this.repo.owner, this.repo.name, request);
  }

  async parseCommentForCommand<T>(
    commentId: number,
    handlers: Record<string, CommmentCommandHandler<T>>,
  ): Promise<T> {
    const comment = await this.octo.rest.issues.getComment({
      repo: this.repo.name,
      owner: this.repo.owner,
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
      permissions = await getRepoPermissions(this.octo, this.repo, login);

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

    const handler = handlers[match[1]];
    if (!handler) {
      throw new NoCommandError(`invalid command "${match[1]}`);
    }
    const issueUrl = comment.data.issue_url;
    const url = new URL(issueUrl);
    const issueId = parseInt(url.pathname.split("/").slice(-1)[0]);

    const issue = await this.octo.rest.issues.get({
      issue_number: issueId,
      repo: this.repo.name,
      owner: this.repo.owner,
    });

    const args = match.slice(2);
    const splitArgs = args.length !== 0 ? args[0].split(" ") : [];
    return handler({
      repo: this.repo,
      comment: {
        id: commentId,
        author: comment.data.user?.login || "",
      },
      issue: {
        id: issueId,
        author: issue.data.user?.login || "",
      },
      body: comment.data.body || "",
      user: {
        login: login || "",
        permissions: permissions || "",
      },
      command: match[1],
      args: {
        raw: args[0],
        splitArgs: splitArgs,
      },
    });
  }
}
