import { Artifact } from "@prisma/client";
import { GithubFetchArgs } from "../../actions/github/fetch/issueFiled.js";
import { GithubEventPointer } from "../../actions/github/upsertOrg/createEventPointersForRepo.js";
import { EventType, prisma } from "../../db/events.js";
import { InvalidInputError } from "../../utils/error.js";

export const getArtifactName = (org: string, repo: string) => `${org}/${repo}`;

export async function getGithubPointer(
  args: GithubFetchArgs,
  eventType: EventType,
): Promise<[Artifact, GithubEventPointer]> {
  const { org, repo } = args;

  if (!org) {
    throw new InvalidInputError("Missing required argument: org");
  }

  if (!repo) {
    throw new InvalidInputError("Missing required argument: org");
  }

  const artifactName = getArtifactName(org, repo);
  const dbArtifact = await prisma.artifact.findFirst({
    where: {
      AND: [
        {
          name: artifactName,
        },
      ],
    },
  });

  if (!dbArtifact) {
    throw new InvalidInputError(
      `No artifact matching ${args.org} and ${args.repo}`,
    );
  }

  const pointer = await prisma.eventPointer.findFirst({
    where: {
      AND: [
        {
          artifactId: dbArtifact.id,
        },
        {
          eventType: eventType,
        },
      ],
    },
  });

  if (!pointer) {
    throw new Error(`No pointer found for artifact and event type`);
  }

  return [dbArtifact, pointer.pointer as any];
}
