import { App, Octokit } from "octokit";
import { stringify } from "envfile";
import * as fsPromise from "fs/promises";
import { logger } from "./utils/logger.js";

export interface Repo {
  name: string;
  owner: string;
}

export interface AppMeta {
  id: number;
  appId: number;
  appSlug: string;
}

export interface OctokitAndAppMeta {
  meta: AppMeta;
  octo: Octokit;
}

export async function getOctokitFor(
  app: App,
  repo: Repo,
): Promise<OctokitAndAppMeta> {
  for await (const { installation } of app.eachInstallation.iterator()) {
    for await (const { octokit, repository } of app.eachRepository.iterator({
      installationId: installation.id,
    })) {
      if (repository.full_name === `${repo.owner}/${repo.name}`) {
        return {
          meta: {
            id: installation.id,
            appId: installation.app_id,
            appSlug: installation.app_slug,
          },
          octo: octokit,
        };
      }
    }
  }
  throw new Error("invalid repo for this github app");
}

export async function getRepoPermissions(
  octo: Octokit,
  repo: Repo,
  login: string,
) {
  const res = await octo.rest.repos.getCollaboratorPermissionLevel({
    owner: repo.owner,
    repo: repo.name,
    username: login,
  });
  return res.data.permission;
}

export class GithubOutput {
  private outputObj: Record<string, unknown>;

  constructor(outputObj: Record<string, unknown> = {}) {
    this.outputObj = outputObj;
  }

  static async write(outputPath: string, obj: Record<string, unknown>) {
    const output = new GithubOutput(obj);
    await output.commit(outputPath);
    return;
  }

  set(key: string, value: unknown) {
    this.outputObj[key] = value;
  }

  async commit(outputPath: string) {
    const outputStr = stringify(this.outputObj);
    return await fsPromise.writeFile(outputPath, outputStr);
  }
}

/**
 * StatusPRComment continuously updates a single comment with the status of a PR.
 */
export class StatusPRComment {
  private app: App;
  private octo: Octokit;
  private repo: Repo;
  private pr: number;
  private messageId: string;

  constructor(
    app: App,
    octo: Octokit,
    repo: Repo,
    pr: number,
    messageId?: string,
  ) {
    this.app = app;
    this.octo = octo;
    this.repo = repo;
    this.pr = pr;
    this.messageId = messageId || "<!-- external-prs-status-comment -->";
  }

  async setStatus(pr: number, message: string) {
    const taggedMessage = `${this.messageId}\n${message}`;

    const appUser = await this.octo.rest.users.getAuthenticated();
    // Search for a comment with the messageId
    // If it doesn't exist, create a comment
    // If it does exist update that comment
    const allCommentRefs = await this.octo.rest.issues.listComments({
      repo: this.repo.name,
      owner: this.repo.owner,
      issue_number: this.pr,
    });

    const appCommentRefs = allCommentRefs.data.filter((c) => {
      return c.user?.id == appUser.data.id;
    });

    if (appCommentRefs.length === 0) {
      await this.octo.rest.issues.createComment({
        owner: this.repo.owner,
        repo: this.repo.name,
        body: taggedMessage,
        issue_number: this.pr,
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

    const matchingComments = comments.filter((c) => {
      const body = c.data.body || "";
      return body.trimStart().indexOf(this.messageId) === 0;
    });

    if (matchingComments.length === 0) {
      await this.octo.rest.issues.createComment({
        owner: this.repo.owner,
        repo: this.repo.name,
        body: taggedMessage,
        issue_number: this.pr,
      });
      return;
    }
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
    await this.octo.rest.issues.updateComment({
      owner: this.repo.owner,
      repo: this.repo.name,
      comment_id: matchingComments[0].data.id,
      body: taggedMessage,
    });
  }
}
