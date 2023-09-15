import { DateTime } from "luxon";
import { GenericError } from "../common/errors.js";
import * as path from "path";
import * as fs from "fs/promises";
import { fileExists } from "../utils/files.js";
import { mkdirp } from "mkdirp";
import {
  doRangesIntersect,
  findMissingRanges,
  Range,
  rangeFromISO,
} from "../utils/ranges.js";

export class CacheDoesNotExist extends GenericError {}

const CACHE_FILE_PATTERN = /\d+.json/;
const CACHE_DIRECTORY_PATTERN =
  /(?<startDate>\d{4}-\d{2}-\d{2}-\d{2})-(?<endDate>\d{4}-\d{2}-\d{2}-\d{2})/;
const DATE_TO_NAME_FORMAT = "yyyy-LL-dd-HH";

// Types for a generic caching mechanism
export type Cacheable<T> = {
  raw: T;

  cacheRange: Range;

  cursor?: any;

  hasNextPage: boolean;
};

type RawCacheable = {
  raw: unknown;
  cacheRange: {
    startDate: string;
    endDate: string;
  };
  cursor?: any;
  hasNextPage: boolean;
};

async function cacheableFromFile<T>(path: string): Promise<Cacheable<T>> {
  const raw = JSON.parse(
    await fs.readFile(path, { encoding: "utf-8" }),
  ) as RawCacheable;
  return {
    raw: raw.raw as T,
    cacheRange: rangeFromISO(raw.cacheRange.startDate, raw.cacheRange.endDate),
    cursor: raw.cursor,
    hasNextPage: raw.hasNextPage,
  };
}

class CachePageDirectory {
  range: Range;
  path: string;

  constructor(range: Range, path: string) {
    this.range = range;
    this.path = path;
  }

  async isValid() {
    return await fileExists(path.join(this.path, "0.json"));
  }

  async pagePaths(): Promise<string[]> {
    const files = await fs.readdir(this.path);
    const pageNumbers: number[] = files
      .filter((f) => {
        return f.match(CACHE_FILE_PATTERN);
      })
      .map((f) => {
        return parseInt(f.split(".")[0]);
      });
    pageNumbers.sort((a, b) => a - b);
    return pageNumbers.map((n) => path.join(this.path, `${n}.json`));
  }

  async *load<T>(): AsyncGenerator<Cacheable<T>> {
    // yield all of the cache directories' pages in order duplicates can occur
    // if the mechanism that has written into the directory structure allows
    // duplicates. We will assume that's fine.
    for (const pagePath of await this.pagePaths()) {
      yield await cacheableFromFile(pagePath);
    }
  }
}

export type TimeSeriesCacheLookup = {
  // Used to put caches in buckets for lookup.
  bucket: string;

  // Usually a hash of the input for the cache
  key: string;

  // Cache range to search for
  range: Range;

  // What is the unit of we should normalize to (only days or hours at this time)
  normalizingUnit: "day" | "hour";
};

export type PageRetreiver<T> = (
  range: Range,
  lastPage?: Cacheable<T>,
) => Promise<Cacheable<T>>;

export interface ITimeSeriesCacheManager {
  load(
    lookup: TimeSeriesCacheLookup,
    page?: number,
  ): Promise<TimeSeriesCacheCollection>;
  write<T>(
    lookup: TimeSeriesCacheLookup,
    item: Cacheable<T>,
    page?: number,
  ): Promise<void>;
}

/**
 * TimeSeriesCacheManager
 *
 * Caches responses so that we can query anything within a specific time range
 * for a given key. This means the key should be something that doesn't change
 * frequently or in a way that is non-deterministic.
 *
 * Caches are stored in the cache directory in the following way on the
 * filesystem:
 *
 *     {cache-dir}/{bucket}/{key}/{startDate}-{endDate}/{pageNumber}.json
 *
 * Minimum resolution of start/end times is hourly minutes and less are ignored.
 */
export class TimeSeriesCacheManager implements ITimeSeriesCacheManager {
  private cacheDir: string;

  constructor(cacheDir: string) {
    this.cacheDir = cacheDir;
  }

  async load(
    lookup: TimeSeriesCacheLookup,
    _page?: number,
  ): Promise<TimeSeriesCacheCollection> {
    const startDateSearch = lookup.range.startDate.startOf(
      lookup.normalizingUnit,
    );
    const endDateSearch = lookup.range.endDate.startOf(lookup.normalizingUnit);
    const normalizedRange = {
      startDate: startDateSearch,
      endDate: endDateSearch,
    };

    // Check if the directory exists
    if (!(await this.fileExists(lookup.bucket, lookup.key))) {
      throw new CacheDoesNotExist(`Cache directory does not exist`, {
        lookup: lookup,
      });
    }

    // List files in the cache. See if any match what we need.
    const allCacheDirectories = await this.listAvailableCacheDirectories(
      lookup.bucket,
      lookup.key,
    );
    const cacheDirectories = allCacheDirectories.filter((cd) => {
      return doRangesIntersect(cd.range, normalizedRange);
    });
    return new TimeSeriesCacheCollection(cacheDirectories, lookup);
  }

  async write<T>(
    lookup: TimeSeriesCacheLookup,
    item: Cacheable<T>,
    page?: number,
  ): Promise<void> {
    const startDateWrite = lookup.range.startDate.startOf(
      lookup.normalizingUnit,
    );
    const endDateWrite = lookup.range.endDate.startOf(lookup.normalizingUnit);
    const cacheDirParts = [
      lookup.bucket,
      lookup.key,
      `${startDateWrite.toFormat(DATE_TO_NAME_FORMAT)}-${endDateWrite.toFormat(
        DATE_TO_NAME_FORMAT,
      )}`,
    ];
    await this.ensureDirectory(...cacheDirParts);

    const pageCachePath = this.cachePath(
      ...[...cacheDirParts, `${page || 0}.json`],
    );
    // This does not validate page numbers so it will just overwrite things.

    const jsonable: RawCacheable = {
      cacheRange: {
        startDate: item.cacheRange.startDate.setZone("utc").toISO()!,
        endDate: item.cacheRange.endDate.setZone("utc").toISO()!,
      },
      cursor: item.cursor,
      hasNextPage: item.hasNextPage,
      raw: item.raw,
    };

    const jsonDump = JSON.stringify(jsonable);
    return await fs.writeFile(pageCachePath, jsonDump, { encoding: "utf-8" });
  }

  private async ensureDirectory(...paths: string[]) {
    return await mkdirp(this.cachePath(...paths));
  }

  private async fileExists(...paths: string[]): Promise<boolean> {
    return await fileExists(this.cachePath(...paths));
  }

  private async listAvailableCacheDirectories(...paths: string[]) {
    const files = await this.listCacheCompatibleDirectories(...paths);
    const cacheDirectories = await Promise.all(
      files.map((f) => {
        return this.loadCachePageDirectory(f, this.cachePath(...[...paths, f]));
      }),
    );

    const validCacheDirectories: CachePageDirectory[] = [];
    for (const dir of cacheDirectories) {
      if (await dir.isValid()) {
        validCacheDirectories.push(dir);
      }
    }
    return validCacheDirectories;
  }

  private async listCacheCompatibleDirectories(...paths: string[]) {
    const names = await fs.readdir(this.cachePath(...paths));

    const filtered = names.filter((f) => {
      if (!f.match(CACHE_DIRECTORY_PATTERN)) {
        return false;
      }
      return true;
    });
    return filtered;
  }

  private cachePath(...paths: string[]) {
    return path.join(this.cacheDir, ...paths);
  }

  private async loadCachePageDirectory(
    name: string,
    path: string,
  ): Promise<CachePageDirectory> {
    const match = CACHE_DIRECTORY_PATTERN.exec(name);

    if (!match?.groups) {
      throw new Error(`Unexpected cache directory name ${name}`);
    }

    const range = {
      startDate: DateTime.fromFormat(
        match.groups.startDate,
        DATE_TO_NAME_FORMAT,
        { zone: "utc" },
      ),
      endDate: DateTime.fromFormat(match.groups.endDate, DATE_TO_NAME_FORMAT, {
        zone: "utc",
      }),
    };
    return new CachePageDirectory(range, path);
  }
}

/**
 * A set of cached files matching a lookup
 */
export class TimeSeriesCacheCollection {
  private _directories: CachePageDirectory[];
  private lookup: TimeSeriesCacheLookup;

  constructor(
    directories: CachePageDirectory[],
    lookup: TimeSeriesCacheLookup,
  ) {
    this._directories = directories;
    this.lookup = lookup;
  }

  missingRanges() {
    return findMissingRanges(
      this.lookup.range.startDate,
      this.lookup.range.endDate,
      this._directories.map((c) => c.range),
    );
  }

  *directories(): Generator<CachePageDirectory> {
    for (const dir of this._directories) {
      yield dir;
    }
  }
}

export class TimeSeriesCacheWrapper {
  private manager: ITimeSeriesCacheManager;

  constructor(manager: ITimeSeriesCacheManager) {
    this.manager = manager;
  }

  /**
   * Loads from cache or through some retreiver callback
   *
   * @param lookup Lookup parameters for the time series cache
   * @param retriever callback to use to load any additional things and automatically cache
   */
  async *loadCachedOrRetrieve<T>(
    lookup: TimeSeriesCacheLookup,
    retriever: PageRetreiver<T>,
  ): AsyncGenerator<Cacheable<T>> {
    // Determine if the lookup matches anything in the cache. If it does not this
    const currentPage = 0;

    const missingQueue: Array<Range & { lastPage?: Cacheable<T> }> = [];
    const response = await this.attemptCacheLoad(lookup, currentPage);
    if (response) {
      // Load everything from cache that we can and then queue the missing pages as needed
      for (const dir of response.directories()) {
        let lastPage: Cacheable<T> | undefined = undefined;

        for await (const page of dir.load<T>()) {
          yield page;
          lastPage = page;
        }

        if (lastPage && lastPage.hasNextPage) {
          // We're missing pages... queue this up for retrieval
          missingQueue.push({
            ...dir.range,
            ...{ lastPage: lastPage },
          });
        }
      }
      missingQueue.push(...response.missingRanges());
    } else {
      missingQueue.push(lookup.range);
    }

    for (const missingRange of missingQueue) {
      let lastPage = missingRange.lastPage;

      while (true) {
        const page = await retriever(missingRange, lastPage);

        // Write the page to cache
        await this.manager.write(lookup, page);

        // Yield the page
        yield page;

        lastPage = page;

        if (!page.hasNextPage) {
          break;
        }
      }
    }
  }

  async attemptCacheLoad(
    lookup: TimeSeriesCacheLookup,
    page: number,
  ): Promise<TimeSeriesCacheCollection | undefined> {
    try {
      const response = await this.manager.load(lookup, page);
      return response;
    } catch (e) {
      if (!(e instanceof CacheDoesNotExist)) {
        throw e;
      }
    }
    return;
  }
}
