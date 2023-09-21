import { ArtifactType, ArtifactNamespace } from "@prisma/client";
import { prisma } from "../../../db/prisma-client.js";
import { getOwnerRepos } from "../../../events/github/getOrgRepos.js";

export async function fetchGithubReposForOrg(orgName: string) {
  const repos = await getOwnerRepos(orgName);
  await prisma.artifact.createMany({
    data: repos.map((repo) => ({
      type: ArtifactType.GIT_REPOSITORY,
      namespace: ArtifactNamespace.GITHUB,
      name: repo.name,
      url: repo.url,
    })),
    skipDuplicates: true,
  });
}

// NOTE: github org names might not be case sensitive
