// Currently just a test file but if it gets committed that wasn't intentional
// but is also just fine
import { handleError } from "../utils/error.js";
import { Argv } from "yargs";
import { ArtifactType, Artifact, Project, Event } from "../index.js";
import _ from "lodash";
import { AppDataSource } from "../db/data-source.js";
import { ProjectRepository } from "../db/project.js";

export type ArtifactsCommonArgs = {
  type?: ArtifactType;
};

export function artifactsCommandGroup(topYargs: Argv) {
  topYargs.command<ArtifactsCommonArgs>(
    "fix-casing",
    "Fixes any duplicate artifact naming errors",
    (yargs) => {
      yargs.option("type", {
        type: "array",
        description: "restrict to specific types",
      });
    },
    (args) => handleError(fixArtifactCasing(args)),
  );
}

export async function fixArtifactCasing(
  _args: ArtifactsCommonArgs,
): Promise<void> {
  const caseInsensitiveTypes: ArtifactType[] = [
    // ArtifactType.CONTRACT_ADDRESS,
    // ArtifactType.EOA_ADDRESS,
    // ArtifactType.GITHUB_ORG,
    // ArtifactType.GITHUB_USER,
    // ArtifactType.GIT_EMAIL,
    ArtifactType.GIT_REPOSITORY,
  ];
  const duplicates = await artifactDuplicates(caseInsensitiveTypes);

  for (const duplicate of duplicates) {
    // Choose a canonical version (currently we choose the one with the lowest id)
    const ids = duplicate.ids;
    ids.sort();

    // Fix the project associations
    const canonicalId = ids[0];

    const projects = await ProjectRepository.find({
      relations: {
        artifacts: true,
      },
      where: {
        artifacts: {
          id: In(ids),
        },
      },
    });

    // Fix all the projects
    for (const project of projects) {
      const found = _.findKey(project.artifacts, { id: canonicalId });
      if (found) {
        continue;
      }
      await ProjectRepository.createQueryBuilder()
        .relation(Project, "artifacts")
        .of(project.id)
        .addAndRemove([ids[0]], ids.slice(1));
    }

    // Move all of the events to the oldest verisons of objects (hopefully
    // there are no duplicates or this will fail) do queries one by one
    await AppDataSource.createQueryBuilder()
      .update(Event)
      .set({ to: { id: canonicalId } })
      .where("toId IN (:...ids)", { ids: ids.slice(1) })
      .execute();

    await AppDataSource.createQueryBuilder()
      .update(Event)
      .set({ from: { id: canonicalId } })
      .where("fromId IN (:...ids)", { ids: ids.slice(1) })
      .execute();
  }
}

async function artifactDuplicates(types: ArtifactType[]) {
  return (await AppDataSource.createQueryBuilder()
    .select()
    .addSelect('lower(a."name")', "name")
    .addSelect('a."namespace"', "namespace")
    .addSelect('a."type"', "type")
    .addSelect('count(a."id")', "count")
    .addSelect('array_agg(a."id")', "ids")
    .from(Artifact, "a")
    .where("a.type IN (:...types)", { types: types })
    .groupBy("1,2,3")
    .having('count(a."id") > 1')
    .getRawMany()) as {
    name: string;
    namespace: string;
    type: string;
    id_count: number;
    ids: number[];
  }[];
}
