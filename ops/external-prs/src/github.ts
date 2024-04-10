import { App, Octokit } from "octokit";
import { stringify } from "envfile";
import * as fsPromise from "fs/promises";

export interface Repo {
  name: string;
  owner: string;
}

export async function getOctokitFor(app: App, repo: Repo): Promise<Octokit> {
  for await (const { installation } of app.eachInstallation.iterator()) {
    for await (const { octokit, repository } of app.eachRepository.iterator({
      installationId: installation.id,
    })) {
      if (repository.full_name === `${repo.owner}/${repo.name}`) {
        return octokit;
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
