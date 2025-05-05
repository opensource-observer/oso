import { CheckRequest, setCheckStatus } from "./checks.js";
import {
  AppMeta,
  OctokitAndAppMeta,
  Repo,
  getRepoPermissions,
} from "./github.js";
import { App, Octokit } from "octokit";
import { logger } from "./utils/logger.js";
import { URL } from "url";

export interface BaseArgs {
  githubAppPrivateKey: string;
  githubAppId: string;
  repo: Repo;
  app: App;
  appUtils: GHAppUtils;
  adminTeamName: string;
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

export type CommentCommandHandler<T> = (command: CommentCommand) => Promise<T>;

/**
 * Convenience utilities for external PRs
 */
export class GHAppUtils {
  private app: App;
  private repo: Repo;
  private adminTeamName: string;
  private octo: Octokit;
  private appMeta: AppMeta;

  constructor(
    app: App,
    repo: Repo,
    adminTeamName: string,
    octoAndMeta: OctokitAndAppMeta,
  ) {
    this.app = app;
    this.repo = repo;
    this.octo = octoAndMeta.octo;
    this.adminTeamName = adminTeamName;
    this.appMeta = octoAndMeta.meta;
  }

  async leaveCommentOnPr(pr: number, comment: string) {
    await this.octo.rest.issues.createComment({
      owner: this.repo.owner,
      repo: this.repo.name,
      body: comment,
      issue_number: pr,
    });
  }

  /**
   * Set a status comment on a PR
   * This will try to keep updating the same comment if it exists
   * You can have multiple comments by setting a `messageId`
   **/
  async setStatusComment(pr: number, message: string, messageId?: string) {
    messageId = messageId || "external-pr-status-comment";
    const messageIdText = `<!-- ${messageId} -->`;
    const taggedMessage = `${messageIdText}\n${message}`;

    const appId = this.appMeta.appId;
    logger.info(`Setting status comment with appId: ${appId}`);
    // Search for a comment with the messageId
    // If it doesn't exist, create a comment
    // If it does exist update that comment
    const allCommentRefs = await this.octo.rest.issues.listComments({
      repo: this.repo.name,
      owner: this.repo.owner,
      issue_number: pr,
    });

    //console.log(allCommentRefs.data.map((c) => c.user));
    const appCommentRefs = allCommentRefs.data.filter((c) => {
      return c.performed_via_github_app?.id === appId;
    });
    //console.log(appCommentRefs);

    // If this app has never commented on this PR, just create it
    if (appCommentRefs.length === 0) {
      await this.octo.rest.issues.createComment({
        owner: this.repo.owner,
        repo: this.repo.name,
        body: taggedMessage,
        issue_number: pr,
      });
      return;
    }

    const comments: Awaited<
      ReturnType<Octokit["rest"]["issues"]["getComment"]>
    >[] = [];

    // Get all app comments
    for (const appCommentRef of appCommentRefs) {
      const appComment = await this.octo.rest.issues.getComment({
        repo: this.repo.name,
        owner: this.repo.owner,
        comment_id: appCommentRef.id,
      });
      comments.push(appComment);
    }

    // Look for the messageIdText
    const matchingComments = comments.filter((c) => {
      const body = c.data.body || "";
      return body.trimStart().indexOf(messageIdText) === 0;
    });

    // Just create it if it doesn't exist yet
    if (matchingComments.length === 0) {
      await this.octo.rest.issues.createComment({
        owner: this.repo.owner,
        repo: this.repo.name,
        body: taggedMessage,
        issue_number: pr,
      });
      return;
    }

    // Delete any duplicate comments with the same messageIdText
    if (matchingComments.length > 1) {
      logger.warn(
        "multiple matching comments found. This isn't treated as an error. Deleting extra comments",
      );
    }
    for (const matchingComment of matchingComments.slice(1)) {
      await this.octo.rest.issues.deleteComment({
        owner: this.repo.owner,
        repo: this.repo.name,
        comment_id: matchingComment.data.id,
      });
    }

    // Update the existing comment
    await this.octo.rest.issues.updateComment({
      owner: this.repo.owner,
      repo: this.repo.name,
      comment_id: matchingComments[0].data.id,
      body: taggedMessage,
    });
  }

  async isLoginOnTeam(login: string, team: string) {
    const teamMembers = await this.octo.rest.teams.listMembersInOrg({
      team_slug: team,
      org: this.repo.owner,
    });

    const teamLogins = teamMembers.data.map((member) =>
      member.login.toLowerCase(),
    );

    // Check the user's membership on the team
    return teamLogins.indexOf(login.toLowerCase()) !== -1;
  }

  async isLoginOnAdminTeam(login: string) {
    logger.info({
      message: "checking admin team membership",
    });
    return this.isLoginOnTeam(login, this.adminTeamName);
  }

  async setCheckStatus(request: CheckRequest) {
    return setCheckStatus(this.octo, this.repo.owner, this.repo.name, request);
  }

  async parseCommentForCommand<T>(
    commentId: number,
    handlers: Record<string, CommentCommandHandler<T>>,
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
      content: comment.data.body,
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
      logger.warn(
        `Valid commands include ${Object.keys(handlers)
          .map((x) => `'${x}'`)
          .join(", ")}`,
      );
      throw new NoCommandError(`invalid command /${match[1]}`);
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
