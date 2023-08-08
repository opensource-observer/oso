//import { prisma } from "../db/prisma-client.js";
import { CommonArgs } from "../utils/api.js";
import { logger } from "../utils/logger.js";
import { fetchData } from "oss-directory";

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
}
