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
    const handles: RecordHandle[] = [];

    for await (const page of response) {
      const days = page.raw;
      for (const download of days) {
        handles.push(
          await this.recorder.record({
            time: DateTime.fromISO(download.day),
            type: {
              name: "DOWNLOADS",
              version: 1,
            },
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
    await this.recorder.wait(handles);
    committer.commit(npmPackage).withHandles(handles);
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
    if (err.statusCode == 404) {
      logger.error(`${name} project cannot be found. skipping`);
      return [];
    }
    if (err.statusCode && err.body) {
      // suppress 404's for now but we should like collect some kinds of warnings for data that is missing
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
    start.startOf("day").toMillis() === resultStart.startOf("day").toMillis() &&
    end.startOf("day").toMillis() === resultEnd.startOf("day").toMillis()
  ) {
    return [...resultDownloads];
  } else if (
    end.startOf("day").toMillis() !== resultEnd.startOf("day").toMillis()
  ) {
    // Assume that NPM will always give us the newest data first
    throw new MalformedDataError(
      `Expected end date ${end.toISO()} but got ${resultEnd.toISO()}`,
    );
  } else {
    // If we didn't get all the data, recurse
    const missingEnd = resultStart.minus({ day: 1 });
    const missingResults = await getDailyDownloads(name, start, missingEnd);
    return [...missingResults, ...resultDownloads];
  }
}
