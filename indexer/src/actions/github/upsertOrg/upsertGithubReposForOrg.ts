import {
  PrismaClient,
  Prisma,
  ArtifactType,
  ArtifactNamespace,
} from "@prisma/client";

import { getOrgRepos } from "../../../utils/github/getOrgRepos.js";

export async function fetchGithubReposForOrg(orgName: string) {
  const prisma = new PrismaClient();

  const existingArtifacts = await prisma.artifact.findMany({
    where: {
      name: {
        startsWith: orgName,
      },
    },
  });

  const repos = await getOrgRepos(orgName);
  const newRepos = repos.filter(
    (repo) =>
      !existingArtifacts.some(
        (artifact) => artifact.url && artifact.url == repo.url,
      ),
  );

  const newArtifacts: Prisma.ArtifactCreateManyInput[] = newRepos.map(
    (repo) => {
      return {
        type: ArtifactType.GIT_REPOSITORY,
        namespace: ArtifactNamespace.GITHUB,
        name: repo.name,
        url: repo.url,
      };
    },
  );

  await prisma.artifact.createMany({
    data: newArtifacts,
  });

  console.log(
    `Created ${newRepos.length} new github repository artifacts for ${orgName}`,
  );
}

// NOTE: github org names might not be case sensitive
