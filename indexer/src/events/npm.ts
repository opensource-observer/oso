import _ from "lodash";
import npmFetch from "npm-registry-fetch";
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
  IArtifactGroupCommitmentProducer,
} from "../scheduler/types.js";
import { Range } from "../utils/ranges.js";
import {
  TimeSeriesCacheLookup,
  TimeSeriesCacheWrapper,
} from "../cacher/time-series.js";
import { In, Repository } from "typeorm";
import { IEventRecorder, RecordHandle } from "../recorder/types.js";
import { DateTime } from "luxon";
import { generateSourceIdFromArray } from "../utils/source-ids.js";

// API endpoint to query
const NPM_HOST = "https://api.npmjs.org/";
// npm was initially released 2010-01-12
// Only get data up to 2 days ago, accounting for incomplete days and time zones
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
    committer: IArtifactGroupCommitmentProducer,
  ): Promise<CollectResponse> {
    const artifacts = await group.artifacts();
    const project = await group.meta();

    for (const npmPackage of artifacts) {
      await this.getEventsForPackage(project, npmPackage, range, committer);
    }
  }

  async getEventsForPackage(
    project: Project,
    npmPackage: Artifact,
    range: Range,
    committer: IArtifactGroupCommitmentProducer,
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
    const recordHandle: RecordHandle[] = [];

    for await (const page of response) {
      const days = page.raw;
      for (const download of days) {
        recordHandle.push(
          await this.recorder.record({
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
    committer.commit(npmPackage).withHandles(recordHandle);
  }
}

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
