//import { prisma } from "../db/prisma-client.js";
import { CommonArgs } from "../utils/api.js";
import { logger } from "../utils/logger.js";
import { fetchData } from "oss-directory";
import { ossUpsertCollection, ossUpsertProject } from "../db/entities.js";

/**
 * Entrypoint arguments
 */
export type ImportOssDirectoryArgs = CommonArgs;

export async function importOssDirectory(
  _args: ImportOssDirectoryArgs,
): Promise<void> {
  logger.info("Importing from 'oss-directory'");
  const { projects, collections } = await fetchData();
  logger.info(
    `Found ${projects.length} projects and ${collections.length} collections`,
  );

  logger.info("Upserting projects...");
  for (let i = 0; i < projects.length; i++) {
    const p = projects[i];
    logger.info(`projects[${i}]: Upserting ${p.slug}`);
    await ossUpsertProject(p);
  }

  logger.info("Upserting collections...");
  for (let i = 0; i < collections.length; i++) {
    const c = collections[i];
    logger.info(`collections[${i}]: Upserting ${c.slug}`);
    await ossUpsertCollection(c);
  }

  logger.info("Done");
}
