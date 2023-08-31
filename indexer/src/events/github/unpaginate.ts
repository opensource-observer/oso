import ora from "ora";
import { graphQLClient } from "./graphQLClient.js";
import { Path, Choose, getPath } from "../../utils/getPath.js";

export type PageInfo = {
  hasNextPage: boolean;
  endCursor: string;
};

// TODO: return type should error if not array
// TODO: pageInfoPath should locate a PageInfo object
// type HasPageInfo<T extends Record<string | number, any>, K extends Path<T>> = Choose<T, K> extends PageInfo ? K : never;

// typescript can't infer T because it's not passed in (like in getPath), and K can't be inferred precisely without writing
// out the entire path again. So we curry the function. Sorry for the mess...
export function unpaginate<T extends Record<string | number, any>>() {
  return async function <K extends Path<T>, A extends Path<T>>(
    query: string,
    dataPath: K,
    pageInfoPath: A,
    variables: any = {},
  ): Promise<Choose<T, K> extends Array<any> ? Choose<T, K> : never> {
    const items: any[] = [];
    for await (const page of unpaginateIterator<T>()(
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

export function unpaginateIterator<T extends Record<string | number, any>>() {
  return async function* <K extends Path<T>, A extends Path<T>>(
    query: string,
    dataPath: K,
    pageInfoPath: A,
    variables: any = {},
  ): AsyncGenerator<UnpaginateResult<T, K>> {
    let cursor = null;

    const spinner = ora("GitHub API").start();
    /* eslint-disable-next-line no-constant-condition */
    while (true) {
      const data = await graphQLClient.request<T>(query, {
        ...variables,
        cursor: cursor,
      });

      yield {
        results: await getPath(data, dataPath),
        raw: data,
      };

      // hacky... slow things down right now
      await sleep(1000);

      const rateLimit: RateLimit = data.rateLimit;
      spinner.suffixText = `: ${rateLimit.remaining}/${rateLimit.limit} credits remaining `;

      if (
        rateLimit.remaining == 0 ||
        rateLimit.remaining - rateLimit.cost <= 0
      ) {
        const timeToReset = Date.parse(rateLimit.resetAt) - Date.now() + 1000;
        console.log(`sleeping until rate limit reset for ${timeToReset}ms`);
        await sleep(timeToReset);
      }

      const pageInfo: PageInfo = getPath(data, pageInfoPath);
      if (!pageInfo.hasNextPage) {
        break;
      }

      cursor = pageInfo.endCursor;
    }
    spinner.stop();
  };
}

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export interface RateLimit {
  limit: number;
  cost: number;
  remaining: number;
  resetAt: string;
}
