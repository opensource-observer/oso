import { ArtifactNamespace, ArtifactType, PrismaClient } from "@prisma/client";
import { createEventPointersForRepo } from "./createEventPointersForRepo.js";

export async function createEventPointersForOrg(orgName: string) {
  const prisma = new PrismaClient();

  const orgRepos = await prisma.artifact.findMany({
    where: {
      AND: [
        {
          name: {
            startsWith: orgName,
          },
        },
        {
          type: ArtifactType.GIT_REPOSITORY,
        },
        {
          namespace: ArtifactNamespace.GITHUB,
        },
      ],
    },
  });

  for (const orgRepo of orgRepos) {
    await createEventPointersForRepo(orgRepo);
  }
}
