import { App, Octokit } from "octokit";

export interface Repo {
  name: string;
  owner: string;
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

export async function getOctokitFor(
  app: App,
  repo: Repo,
): Promise<Octokit | void> {
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
