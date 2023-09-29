import { Octokit } from "octokit";
import { WorkerSpawner } from "./types.js";
import _ from "lodash";

export interface GithubWorkerSpawnerOptions {
  owner: string;
  repo: string;
  workflowId: string;
  ref: string;
}

export class GithubWorkerSpawner implements WorkerSpawner {
  private gh: Octokit;
  private options: GithubWorkerSpawnerOptions;

  constructor(gh: Octokit, options: GithubWorkerSpawnerOptions) {
    this.gh = gh;
    this.options = options;
  }

  async spawn(group?: string): Promise<void> {
    await this.gh.rest.actions.createWorkflowDispatch({
      owner: this.options.owner,
      repo: this.options.repo,
      workflow_id: this.options.workflowId,
      ref: this.options.ref,
      inputs: {
        group: group,
      },
    });
  }
}
