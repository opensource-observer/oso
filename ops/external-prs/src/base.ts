import { CheckRequest, setCheckStatus } from "./checks.js";
import { Repo } from "./github.js";
import { App, Octokit } from "octokit";

export interface BaseArgs {
  githubAppPrivateKey: string;
  githubAppId: string;
  repo: Repo;
  app: App;
  appUtils: GHAppUtils;
}

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
}
