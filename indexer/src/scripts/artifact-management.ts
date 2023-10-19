/* eslint no-restricted-properties: 0 */
// Currently just a test file but if it gets committed that wasn't intentional
// but is also just fine
import { handleError } from "../utils/error.js";
import { Argv } from "yargs";
import {
  ArtifactType,
  Project,
  Event,
  EventPointer,
  Artifact,
} from "../index.js";
import _ from "lodash";
import { AppDataSource } from "../db/data-source.js";
import { In } from "typeorm";
import { ArtifactRepository } from "../db/artifacts.js";
import { Brand } from "utility-types";
import inquirer from "inquirer";
import { ProjectRepository } from "../db/project.js";
import { CollectionRepository } from "../db/collection.js";

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
    ArtifactType.FACTORY_ADDRESS,
    ArtifactType.CONTRACT_ADDRESS,
    ArtifactType.EOA_ADDRESS,
    ArtifactType.SAFE_ADDRESS,
    ArtifactType.GITHUB_ORG,
    ArtifactType.GITHUB_USER,
    ArtifactType.GIT_EMAIL,
    ArtifactType.GIT_REPOSITORY,
  ];
  const artifactDupes = await ArtifactRepository.duplicates(
    caseInsensitiveTypes,
  );
  let artifactsNonCanonical = await ArtifactRepository.nonCanonical(
    caseInsensitiveTypes,
  );
  const projectsDupes = await ProjectRepository.duplicates();
  const projectsNonCanonical = await ProjectRepository.nonCanonical();
  const collectionsDupes = await CollectionRepository.duplicates();
  const collectionsNonCanonical = await CollectionRepository.nonCanonical();
  console.log(`Found ${collectionsDupes.length} duplicated projects`);
  console.log(
    `Found ${collectionsNonCanonical.length} collections without proper canonical naming`,
  );
  console.log(`Found ${projectsDupes.length} duplicated projects for types:`);
  console.log(
    `Found ${projectsNonCanonical.length} projects without proper canonical name`,
  );
  console.log(`Found ${artifactDupes.length} duplicated artifacts for types:`);
  caseInsensitiveTypes.forEach((t) => {
    console.log(`    - ${t}`);
  });
  console.log(
    `Found ${artifactsNonCanonical.length} artifacts without proper canonical name`,
  );

  if (projectsNonCanonical.length > 0) {
    console.warn(
      "There is currently no solution for projects without canonical names",
    );
  }
  if (collectionsNonCanonical.length > 0) {
    console.warn(
      "There is currently no solution for collections without canonical names",
    );
  }
  console.log(artifactsNonCanonical);

  if (artifactDupes.length === 0 && artifactsNonCanonical.length === 0) {
    console.log("");
    console.log("Nothing to do");
    console.log("");
    return process.exit(0);
  }

  const answer = await inquirer.prompt({
    type: "confirm",
    name: "confirm",
    message: "Fix these duplicates now?",
  });
  if (!answer.confirm) {
    console.log("");
    console.log("Not fixing for now.");
    console.log("");
    return process.exit(0);
  }

  await fixAnyGitEmailsAndNames();

  // Fix dupes first
  if (artifactDupes.length > 0) {
    await fixArtifactDuplicates(caseInsensitiveTypes);
    artifactsNonCanonical = await ArtifactRepository.nonCanonical(
      caseInsensitiveTypes,
    );
  }

  if (artifactsNonCanonical.length > 0) {
    await fixNonCanonicalArtifacts(caseInsensitiveTypes);
  }
}

async function fixAnyGitEmailsAndNames() {
  // Punts on git emails by adding a prefix `unverified:email:` before the name
  const r1 = await AppDataSource.query(`
    update artifact a
    set "name" = format('unverified:git:data:email:%s', a."name")
    where a."type" = 'GIT_EMAIL' AND a."name" NOT LIKE 'unverified:git:data:%'
  `);
  console.log("changed names of GIT_EMAIL (that are not emails)");
  console.log(r1);

  const r2 = await AppDataSource.query(`
    update artifact a
    set "name" = format('unverified:git:data:name:%s', a."name")
    where a."type" = 'GIT_NAME' AND a."name" NOT LIKE 'unverified:git:data:%'
  `);

  console.log("changed names of GIT_NAME");
  console.log(r2);
}

async function fixNonCanonicalArtifacts(types: ArtifactType[]): Promise<void> {
  await AppDataSource.createQueryBuilder()
    .update(Artifact)
    .set({ name: () => 'lower("name")' })
    .where("type IN (:...types)", { types: types })
    //.andWhere('lower("name") NOT IN (:...ignore)', { ignore: ignoreNames })
    .execute();
}

async function fixArtifactDuplicates(types: ArtifactType[]): Promise<void> {
  const duplicates = await ArtifactRepository.duplicates(types);

  for (const duplicate of duplicates) {
    const artifactStr = `Artifact[name=${duplicate.name},ns=${duplicate.namespace},t=${duplicate.type}]`;
    console.log("---------------------------");
    console.log(`Fixing ${artifactStr}`);

    // Fix duplicates in a transaction for safety
    await AppDataSource.transaction(async (manager) => {
      // Choose a canonical version (currently we choose the one with the lowest id)
      const ids = duplicate.ids;
      ids.sort();

      // Fix the project associations
      const canonicalId = ids[0];
      console.log(`${artifactStr}: canonical id set to ${canonicalId}`);
      const nonCanonicalIds = ids.slice(1);

      const projectRepo = manager.getRepository(Project);

      // Find all projects that happen to have one of these (or all of these)
      // artifacts
      const projects = await projectRepo.find({
        relations: {
          artifacts: true,
        },
        where: {
          artifacts: {
            id: In(ids),
          },
        },
      });
      console.log(
        `${artifactStr}: Found ${projects.length} project(s) with associations`,
      );

      // Fix all the projects
      for (const project of projects) {
        await projectRepo
          .createQueryBuilder()
          .relation(Project, "artifacts")
          .of(project.id)
          .remove(nonCanonicalIds);

        const found = _.findKey(project.artifacts, { id: canonicalId });
        if (!found) {
          await projectRepo
            .createQueryBuilder()
            .relation(Project, "artifacts")
            .of(project.id)
            .add([ids[0]]);
        }
      }

      // Move all of the events to the oldest versions of objects (hopefully
      // there are no duplicates or this will fail) do queries one by one
      const toRes = await manager
        .createQueryBuilder()
        .update(Event)
        .set({ to: { id: canonicalId } })
        .where("toId IN (:...ids)", { ids: nonCanonicalIds })
        .execute();
      console.log(
        `${artifactStr}: Updated ${toRes.affected} event(s) using nonCanonicalIds for toId`,
      );

      const forRes = await manager
        .createQueryBuilder()
        .update(Event)
        .set({ from: { id: canonicalId } })
        .where("fromId IN (:...ids)", { ids: nonCanonicalIds })
        .execute();
      console.log(
        `${artifactStr}: Updated ${forRes.affected} event(s) using nonCanonicalIds for forId`,
      );

      // Find duplicates in the event pointers.
      const epDupesRes = (await manager
        .createQueryBuilder()
        .select()
        .addSelect("ep.collector", "collector")
        .addSelect("ep.startDate", "startDate")
        .addSelect("ep.endDate", "endDate")
        .addSelect('count(ep."id")', "count")
        .addSelect('array_agg(ep."id")', "ids")
        .addSelect('array_agg(ep."artifactId")', "artifactIds")
        .from(EventPointer, "ep")
        .where("ep.artifactId IN (:...ids)", { ids: ids })
        .groupBy("1,2,3")
        .having('count(ep."id") > 1')
        .getRawMany()) as {
        collector: string;
        startDate: string;
        endDate: string;
        count: number;
        ids: number[];
        artifactIds: number[];
      }[];

      // Duplicate pointers need to be merged into a single pointer for the current object
      // Currently this doesn't do any merging of pointers that intersect.
      for (const dupedEp of epDupesRes) {
        // If the canonicalId is not in the set. Set that one.
        const canonicalIndex = dupedEp.artifactIds.indexOf(canonicalId);

        const epIndexToKeep = canonicalIndex === -1 ? 0 : canonicalIndex;
        const epIdsToDelete = dupedEp.ids.filter((d, i) => {
          return i != epIndexToKeep;
        });

        // Delete everything that isn't the one we're keeping
        const delRes = await manager.getRepository(EventPointer).delete({
          id: In(epIdsToDelete),
        });
        console.log(
          `${artifactStr}: Deleting ${delRes.affected} duplicate event pointers`,
        );

        // Update the epIdToKeep
        const ensureRes = await manager
          .createQueryBuilder()
          .update(EventPointer)
          .set({ artifact: { id: canonicalId } })
          .where("id = :id", { id: dupedEp.ids[epIndexToKeep] })
          .execute();
        if (ensureRes.affected && ensureRes.affected > 0) {
          console.log(
            `${artifactStr}: updated EventPointer[${dupedEp.ids[epIndexToKeep]}] to point to the canonical artifact`,
          );
        }
      }

      const epRes = await manager
        .createQueryBuilder()
        .update(EventPointer)
        .set({ artifact: { id: canonicalId } })
        .where("artifactId IN (:...ids)", { ids: nonCanonicalIds })
        .execute();
      console.log(`${artifactStr}: Fixed ${epRes.affected} event pointers`);

      // Rename the artifact if it's not the `lowercase` version of the artifact.
      // Ensure there are zero events from anything but the canonical version
      const count = await manager
        .getRepository(Event)
        .createQueryBuilder("event")
        .where("event.toId IN (:...toIds)", { toIds: nonCanonicalIds })
        .orWhere("event.fromId IN (:...fromIds)", { fromIds: nonCanonicalIds })
        .getCount();
      if (count !== 0) {
        throw new Error("failed to update all events. Failing transaction");
      }

      const artifactRepo = manager.withRepository(ArtifactRepository);

      console.log(`${artifactStr}: Removing nonCanonicalIds`);
      // Delete all of the nonCanonical artifacts
      const delRes = await artifactRepo.delete({
        id: In(nonCanonicalIds),
      });
      if (delRes.affected !== nonCanonicalIds.length) {
        throw new Error("deletion did not run as expected");
      }

      // Ensure the name of the canonical version is lowercased
      await artifactRepo.update(
        {
          id: canonicalId as Brand<number, "ArtifactId">,
        },
        {
          name: duplicate.name.toLowerCase(),
        },
      );
      console.log(`${artifactStr}: changes committed`);
    }).catch((err) => {
      console.log(
        `${artifactStr}: encountered an error. changes not committed`,
      );
      console.error(err);
      throw err;
    });
  }
}
