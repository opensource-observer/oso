import { Path, Choose, getPath } from "./getPath.js";
import { GraphQLClient } from "graphql-request";

export type PageInfo = {
  hasNextPage: boolean;
  endCursor: string;
};

// TODO: return type should error if not array
// TODO: pageInfoPath should locate a PageInfo object
// type HasPageInfo<T extends Record<string | number, any>, K extends Path<T>> = Choose<T, K> extends PageInfo ? K : never;

// typescript can't infer T because it's not passed in (like in getPath), and K can't be inferred precisely without writing
// out the entire path again. So we curry the function. Sorry for the mess...
export function unpaginate<T extends Record<string | number, any>>(
  client: GraphQLClient,
) {
  return async function <K extends Path<T>, A extends Path<T>>(
    query: string,
    dataPath: K,
    pageInfoPath: A,
    variables: any = {},
  ): Promise<Choose<T, K> extends Array<any> ? Choose<T, K> : never> {
    const items: any[] = [];
    for await (const page of unpaginateIterator<T>(client)(
      query,
      dataPath,
      pageInfoPath,
      variables,
    )) {
      items.push(...(page.results as any[]));
    }
    return items as any;
  };
}

export type UnpaginateResult<
  T extends Record<string | number, any>,
  K extends Path<T>,
> = {
  results: Choose<T, K> extends Array<any> ? Choose<T, K> : never;
  raw: unknown;
};

export function unpaginateIterator<T extends Record<string | number, any>>(
  client: GraphQLClient,
) {
  return async function* <K extends Path<T>, A extends Path<T>>(
    query: string,
    dataPath: K,
    pageInfoPath: A,
    variables: any = {},
  ): AsyncGenerator<UnpaginateResult<T, K>> {
    let cursor = null;

    /* eslint-disable-next-line no-constant-condition */
    while (true) {
      const data = await client.request<T>(query, {
        ...variables,
        cursor: cursor,
      });

      yield {
        results: await getPath(data, dataPath),
        raw: data,
      };

      // hacky... slow things down right now
      await sleep(250);

      const rateLimit: RateLimit = data.rateLimit;

      if (
        rateLimit.remaining == 0 ||
        rateLimit.remaining - rateLimit.cost <= 0
      ) {
        const timeToReset = Date.parse(rateLimit.resetAt) - Date.now() + 1000;
        await sleep(timeToReset);
      }

      const pageInfo: PageInfo = getPath(data, pageInfoPath);
      if (!pageInfo.hasNextPage) {
        break;
      }

      if (cursor === pageInfo.endCursor) {
        throw new Error("the cursor is not changing. please fix your query");
      }

      cursor = pageInfo.endCursor;
    }
  };
}

export function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export interface RateLimit {
  limit: number;
  cost: number;
  remaining: number;
  resetAt: string;
}

/**
 * asyncBatch creates batches of a given array for processing. This function
 * awaits the callback for every batch.
 *
 * @param arr - The array to process in batches
 * @param batchSize - The batch size
 * @param cb - The async callback
 * @returns
 */
export async function asyncBatch<T, R>(
  arr: T[],
  batchSize: number,
  cb: (batch: T[], batchLength: number, batchNumber: number) => Promise<R>,
): Promise<R[]> {
  let batch = [];
  let batchNumber = 0;
  const results: R[] = [];
  for (const item of arr) {
    batch.push(item);

    if (batch.length >= batchSize) {
      const batchResult = await cb(batch, batch.length, batchNumber);
      results.push(batchResult);
      batchNumber += 1;
      batch = [];
    }
  }
  if (batch.length > 0) {
    const batchResult = await cb(batch, batch.length, batchNumber);
    results.push(batchResult);
    batch = [];
  }
  return results;
}
