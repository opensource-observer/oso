//import { prisma } from "../db/prisma-client.js";
import { CommonArgs } from "../utils/api.js";
//import { normalizeToObject } from "../utils/common.js";
//import { logger } from "../utils/logger.js";
//import { FETCHER_REGISTRY } from "../cli.js";

/**
 * Entrypoint arguments
 */
export type RunAutocrawlArgs = CommonArgs;

export async function runAutocrawl(_args: RunAutocrawlArgs): Promise<void> {
  /**
  // Get all pointers marked for autocrawl
  const pointers = await prisma.eventPointer.findMany({
    where: {
      autocrawl: true,
    },
  });

  // Iterate over pointers and call the appropriate function
  const summarize = async (
    p: Promise<ApiReturnType>,
  ) => {
    const result = await p;
    return {
      ...result,
    };
  };
  const promises = pointers.map(async (evtSrcPtr) => {
    const { queryCommand, queryArgs } = evtSrcPtr;
    logger.info(
      `Running autocrawl for ${queryCommand} with args ${JSON.stringify(
        queryArgs,
      )}`,
    );
    const action = FETCHER_REGISTRY.find((f) => f.command === queryCommand);
    if (!action) {
      logger.warn(`Unknown queryCommand: ${queryCommand}`);
      return;
    }
    return summarize(
      action.func(normalizeToObject(queryArgs)),
    );
  });
  */

  // Go do it
  const promises: Promise<void>[] = [];
  console.log(await Promise.all(promises));
}
