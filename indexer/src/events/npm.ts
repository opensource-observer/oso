import _ from "lodash";
import npmFetch from "npm-registry-fetch";
//import { EventType } from "@prisma/client";
//port { getEventSourcePointer, insertData } from "../db/events.js";
import { ensureString, ensureArray, ensureNumber } from "../utils/common.js";
import { MalformedDataError } from "../utils/error.js";
import { logger } from "../utils/logger.js";
import { ProjectArtifactsCollector } from "../scheduler/common.js";
import {
  Project,
  Artifact,
  ArtifactType,
  ArtifactNamespace,
  EventType,
} from "../index.js";
import {
  IArtifactGroup,
  CollectResponse,
  CommitArtifactCallback,
} from "../scheduler/types.js";
import { Range } from "../utils/ranges.js";
import {
  TimeSeriesCacheLookup,
  TimeSeriesCacheWrapper,
} from "../cacher/time-series.js";
import { In, Repository } from "typeorm";
import { IEventRecorder } from "../recorder/types.js";
import { DateTime } from "luxon";
import { RecordResponse } from "../recorder/recorder.js";
import { generateSourceIdFromArray } from "../utils/source-ids.js";

// API endpoint to query
const NPM_HOST = "https://api.npmjs.org/";
// npm was initially released 2010-01-12
// const DEFAULT_START_DATE = "2010-01-01";
// const NPM_DOWNLOADS_COMMAND = "npmDownloads";
// // Only get data up to 2 days ago, accounting for incomplete days and time zones
// const TODAY_MINUS = 2;

export interface NPMCollectorOptions {
  cacheOptions: {
    bucket: string;
  };
}

export const DefaultNPMCollectorOptions: NPMCollectorOptions = {
  cacheOptions: {
    bucket: "npm-downloads",
  },
};

export class NpmDownloadCollector extends ProjectArtifactsCollector {
  private options: NPMCollectorOptions;

  constructor(
    projectRepository: Repository<Project>,
    recorder: IEventRecorder,
    cache: TimeSeriesCacheWrapper,
    options?: Partial<NPMCollectorOptions>,
  ) {
    super(projectRepository, recorder, cache, {
      type: In([ArtifactType.NPM_PACKAGE]),
      namespace: ArtifactNamespace.NPM_REGISTRY,
    });

    this.options = _.merge(DefaultNPMCollectorOptions, options);
  }

  async collect(
    group: IArtifactGroup<Project>,
    range: Range,
    commitArtifact: CommitArtifactCallback,
  ): Promise<CollectResponse> {
    const artifacts = await group.artifacts();
    const project = await group.meta();

    for (const npmPackage of artifacts) {
      await this.getEventsForPackage(
        project,
        npmPackage,
        range,
        commitArtifact,
      );
    }
  }

  async getEventsForPackage(
    project: Project,
    npmPackage: Artifact,
    range: Range,
    commitArtifact: CommitArtifactCallback,
  ) {
    const response = this.cache.loadCachedOrRetrieve<DayDownloads[]>(
      TimeSeriesCacheLookup.new(
        `${this.options.cacheOptions.bucket}/${project.slug}`,
        [npmPackage.name],
        range,
      ),
      async (missing) => {
        const downloads = await getDailyDownloads(
          npmPackage.name,
          missing.range.startDate,
          missing.range.endDate,
        );
        return {
          raw: downloads,
          cacheRange: missing.range,
          hasNextPage: false,
        };
      },
    );
    const recordPromises: Promise<RecordResponse>[] = [];

    for await (const page of response) {
      const days = page.raw;
      for (const download of days) {
        recordPromises.push(
          this.recorder.record({
            time: DateTime.fromISO(download.day),
            type: EventType.DOWNLOADS,
            to: npmPackage,
            sourceId: generateSourceIdFromArray([
              "NPM_DOWNLOADS",
              npmPackage.name,
              download.day,
            ]),
            amount: download.downloads,
          }),
        );
      }
    }
    await Promise.all(recordPromises);
    await commitArtifact(npmPackage);
  }
}

// /**
//  * What we expect to store in the EventSourcePointer DB table
//  */
// interface NpmEventSourcePointer {
//   lastDate: string;
// }

// const makeNpmEventSourcePointer = (lastDate: Dayjs): NpmEventSourcePointer => ({
//   lastDate: formatDate(lastDate),
// });

interface DayDownloads {
  downloads: number;
  day: string;
}

function createDayDownloads(x: any): DayDownloads {
  return {
    downloads: ensureNumber(x.downloads),
    day: ensureString(x.day),
  };
}

// /**
//  * Get the artifact and organization for a package, creating it if it doesn't exist
//  *
//  * @param packageName npm package name
//  * @returns Artifact
//  */
// async function getArtifactOrganization(packageName: string) {
//   // Get package.json
//   logger.debug(`Fetching package.json`);
//   const pkgManifest: any = await npmFetch.json(`/ ${ packageName } / latest`);
//   //console.log(JSON.stringify(pkgManifest, null, 2));

//   // Check if the organization exists
//   const repoUrl = pkgManifest?.repository?.url ?? "";
//   logger.info(`Repository URL: ${ repoUrl }`);
//   const { owner: githubOrg } = parseGitHubUrl(repoUrl) ?? {};
//   if (!githubOrg) {
//     logger.warn(`Unable to find the GitHub organization for ${ packageName }`);
//   } else {
//     logger.info(`GitHub organization for ${ packageName }: ${ githubOrg } `);
//   }

//   // Upsert the organization and artifact into the database
//   logger.debug("Upserting organization and artifact into database");
//   const dbArtifact = upsertNpmPackage(packageName);
//   logger.info("Inserted artifact into DB", dbArtifact);

//   return dbArtifact;
// }

/**
 * When you query the NPM API with a range, it may only return a subset of dates you want
 * This function lets us recurse until we get everything
 * @param name npm package name
 * @param start date inclusive
 * @param end date inclusive
 */
async function getDailyDownloads(
  name: string,
  start: DateTime,
  end: DateTime,
): Promise<DayDownloads[]> {
  const dateRange = `${start.toISODate()}:${end.toISODate()} `;
  const endpoint = `/downloads/range/${dateRange}/${name}`;
  logger.debug(`Fetching ${endpoint}`);
  let results: Record<string, unknown>;
  try {
    results = await npmFetch.json(endpoint, { registry: NPM_HOST });
  } catch (e) {
    const err = e as { statusCode?: number; body?: { error?: string } };
    logger.warn("Error fetching from NPM API: ", err);
    if (err.statusCode && err.body) {
      if (
        err.statusCode == 400 &&
        err.body.error?.indexOf("end date > start date") !== -1
      ) {
        logger.debug(
          `npm is at the limit of all available history for project ${name}`,
        );
        return [];
      }
    }
    throw err;
  }
  //logger.info(JSON.stringify(fetchResults, null, 2));
  const resultStart = DateTime.fromISO(ensureString(results.start), {
    zone: "utc",
  });
  const resultEnd = DateTime.fromISO(ensureString(results.end), {
    zone: "utc",
  });
  const resultDownloads = ensureArray(results.downloads).map(
    createDayDownloads,
  );
  logger.info(
    `Got ${
      resultDownloads.length
    } results from ${resultStart.toISODate()} to ${resultEnd.toISODate()}`,
  );

  // If we got all the data, we're good
  if (
    start.startOf("day").equals(resultStart.startOf("day")) &&
    end.startOf("day").equals(resultEnd.startOf("day"))
  ) {
    return [...resultDownloads];
  } else if (!end.startOf("day").equals(resultEnd.startOf("day"))) {
    // Assume that NPM will always give us the newest data first
    throw new MalformedDataError(
      `Expected end date ${end.toISODate()} but got ${resultEnd.toISODate()}`,
    );
  } else {
    // If we didn't get all the data, recurse
    const missingEnd = resultStart.minus({ day: 1 });
    const missingResults = await getDailyDownloads(name, start, missingEnd);
    return [...missingResults, ...resultDownloads];
  }
}

// /**
//  * Checks to see if the downloads are missing any days between start and end
//  * @param downloads
//  * @param start
//  * @param end
//  * @returns
//  */
// export function getMissingDays(
//   downloads: DayDownloads[],
//   start: Dayjs,
//   end: Dayjs,
// ): Dayjs[] {
//   if (start.isAfter(end, "day")) {
//     throw new InvalidInputError(
//       `Start date ${formatDate(start)} is after end date ${formatDate(end)}`,
//     );
//   }

//   // According to spec, searches must be sublinear
//   const missingDays: Dayjs[] = [];
//   const dateSet = new Set(downloads.map((d) => d.day));
//   for (
//     let datePtr = dayjs(start);
//     datePtr.isBefore(end, "day") || datePtr.isSame(end, "day");
//     datePtr = datePtr.add(1, "day")
//   ) {
//     if (!dateSet.has(formatDate(datePtr))) {
//       missingDays.push(datePtr);
//     }
//   }
//   return missingDays;
// }

// /**
//  * Checks whether there are any duplicate days in the downloads
//  * @param downloads
//  */
// export function hasDuplicates(downloads: DayDownloads[]): boolean {
//   const dates = downloads.map((d) => d.day);
//   const deduplicated = _.uniq(dates);
//   return dates.length !== deduplicated.length;
// }

// /**
//  * Entrypoint arguments
//  */
// export type NpmDownloadsArgs = Partial<
//   CommonArgs & {
//     name: string;
//   }
// >;

// /**
//  * Get all of the daily downloads for a package
//  * @param args
//  */
// export const npmDownloads: EventSourceFunction<NpmDownloadsArgs> = async (
//   args: NpmDownloadsArgs,
// ): Promise<ApiReturnType> => {
//   const { name, autocrawl } = args;

//   if (!name) {
//     throw new InvalidInputError("Missing required argument: name");
//   }
//   logger.info(`NPM Downloads: fetching for ${name}`);

//   // Add the organization and artifact into the database
//   const dbArtifact = await getArtifactOrganization(name);

//   // Get the latest event source pointer
//   logger.debug("Getting latest event source pointer");
//   const previousPointer = await getEventSourcePointer<NpmEventSourcePointer>(
//     dbArtifact.id,
//     EventType.DOWNLOADS,
//   );
//   logger.info(`EventSourcePointer: ${JSON.stringify(previousPointer)}`);

//   // Start 1 day after the last date we have
//   const start = dayjs(previousPointer.lastDate ?? DEFAULT_START_DATE).add(
//     1,
//     "day",
//   );
//   // Today's counts may not yet be complete
//   const end = dayjs().subtract(TODAY_MINUS, "day");
//   logger.info(
//     `Fetching from start=${formatDate(start)} to end=${formatDate(
//       end,
//     )}. Today is ${formatDate(dayjs())}`,
//   );

//   // Short circuit if we're already up to date
//   if (end.isBefore(start, "day")) {
//     return {
//       _type: "upToDate",
//       cached: true,
//     };
//   }

//   // Retrieve any missing data
//   const downloads: DayDownloads[] = await getDailyDownloads(name, start, end);

//   // Check for correctness of data
//   assert(!hasDuplicates(downloads), "Duplicate dates found in result");
//   // If this is the first time running this query, just check that we have the last day
//   const missingDays = !previousPointer.lastDate
//     ? getMissingDays(downloads, end, end)
//     : getMissingDays(downloads, start, end);
//   assert(
//     missingDays.length === 0,
//     `Missing dates found in result: ${missingDays.map(formatDate).join(", ")}`,
//   );

//   // Transform the data into the format we want to store
//   const dbEntries = downloads.map((d) => ({
//     artifactId: dbArtifact.id,
//     eventType: EventType.DOWNLOADS,
//     eventTime: dayjs(d.day).toDate(),
//     amount: d.downloads,
//   }));

//   // Populate the database
//   await insertData(
//     dbArtifact.id,
//     EventType.DOWNLOADS,
//     dbEntries,
//     previousPointer,
//     safeCast<Partial<NpmEventSourcePointer>>(makeNpmEventSourcePointer(end)),
//     NPM_DOWNLOADS_COMMAND,
//     safeCast<Partial<NpmDownloadsArgs>>(args),
//     autocrawl,
//   );

//   // Return results
//   return {
//     _type: "success",
//     count: downloads.length,
//   };
// };

// export const NpmDownloadsInterface: ApiInterface<NpmDownloadsArgs> = {
//   command: NPM_DOWNLOADS_COMMAND,
//   func: npmDownloads,
// };
