import { fetchData } from "oss-directory";
import {
  getCollectionBySlug,
  getProjectBySlug,
  ossUpsertCollection,
  ossUpsertProject,
} from "../db/entities.js";
import { CommonArgs } from "../utils/api.js";
import { logger } from "../utils/logger.js";
import { CollectionRepository } from "../db/collection.js";
import { In, IsNull } from "typeorm";
import _ from "lodash";

/**
 * Entrypoint arguments
 */
export type ImportOssDirectoryArgs = CommonArgs & {
  skipExisting?: boolean;
};

export async function importOssDirectory(
  args: ImportOssDirectoryArgs,
): Promise<void> {
  const { skipExisting } = args;
  logger.info("Importing from 'oss-directory'");
  const { projects, collections } = await fetchData();
  logger.info(
    `Found ${projects.length} projects and ${collections.length} collections`,
  );

  logger.info("Upserting projects...");
  for (let i = 0; i < projects.length; i++) {
    const p = projects[i];
    // This is not ideal but for now this will ensure the slug is normalized
    p.slug = p.slug.toLowerCase();
    if (skipExisting && (await getProjectBySlug(p.slug))) {
      logger.info(
        `projects[${i}]: Skipping ${p.slug} because it already exists`,
      );
      continue;
    }
    logger.info(`projects[${i}]: Upserting ${p.slug}`);
    try {
      const result = await ossUpsertProject(p);
      logger.info(`projects[${i}]: Added ${result.added} artifacts`);
      logger.info(`projects[${i}]: Removed ${result.removed} artifacts`);
    } catch (e) {
      logger.error(
        `projects[${i}]: error occured processing project ${p.slug}. Skipping with error: ${e}`,
      );
    }
  }

  const currentCollections = await CollectionRepository.find({
    where: {
      type: { name: "OSS_DIRECTORY" },
      deletedAt: IsNull(),
    },
  });

  // Calculate the removed collections
  const removedCollections = _.differenceWith(
    currentCollections,
    collections,
    (a, b) => {
      return a.slug === b.slug;
    },
  );

  if (removedCollections.length > 0) {
    logger.info(`removing ${removedCollections.length} deleted collections`);

    // Mark the collections as deleted
    await CollectionRepository.update(
      {
        id: In(removedCollections.map((c) => c.id)),
      },
      {
        deletedAt: new Date(),
      },
    );
  }

  logger.info("Upserting collections...");
  for (let i = 0; i < collections.length; i++) {
    const c = collections[i];
    c.slug = c.slug.toLowerCase();
    if (skipExisting && (await getCollectionBySlug(c.slug))) {
      logger.info(
        `collections[${i}]: Skipping ${c.slug} because it already exists`,
      );
      continue;
    }
    logger.info(`collections[${i}]: Upserting ${c.slug}`);
    try {
      const result = await ossUpsertCollection(c);
      logger.info(`collections[${i}]: Added ${result.added} artifacts`);
      logger.info(`collections[${i}]: Removed ${result.removed} artifacts`);
    } catch (e) {
      logger.error(
        `collections[${i}]: error occured processing colelction ${c.slug}. Skipping with error: ${e}`,
      );
    }
  }

  logger.info("Done");
}
