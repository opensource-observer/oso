import {
  Artifact,
  ArtifactNamespace,
  ArtifactType,
  EventType,
  Job,
  JobExecutionStatus,
} from "../db/orm-entities.js";
import { IEventRecorder, IEventTypeStrategy } from "../recorder/types.js";
import { Range, findMissingRanges, rangeFromDates } from "../utils/ranges.js";
import { EventPointerManager } from "./pointers.js";
import { TimeSeriesCacheWrapper } from "../cacher/time-series.js";
import { logger } from "../utils/logger.js";
import {
  JobAlreadyQueued,
  JobExecutionRepository,
  JobsRepository,
} from "../db/jobs.js";
import { DateTime } from "luxon";
import _ from "lodash";
import { INDEXER_SPAWN } from "../config.js";
import { writeFile, readFile, unlink } from "fs/promises";
import path from "path";
import { fileExists } from "../utils/files.js";
import { mkdirp } from "mkdirp";

export type ArtifactGroup = {
  details: unknown;
  artifacts: Artifact[];
};

export type ErrorsList = unknown[];

type LockData = {
  execution: {
    id: number;
  };
  group: string;
};

/**
 * The interface for the scheduler that manages all of the schedules for jobs
 */
export interface ICollector {
  // Yield arrays of artifacts that this collector monitors. This is an async
  // generator so that artifacts can be yielded in groups if needed.
  groupedArtifacts(): AsyncGenerator<ArtifactGroup>;

  collect(
    group: ArtifactGroup,
    range: Range,
    commitArtifact: (artifact: Artifact) => Promise<void>,
  ): Promise<void>;
}

/**
 * Rudimentary service locator that uses names to register services. This isn't
 * ideal but will work for now to ensure we can do dependency injection.
 */
export interface IConfig {
  get<T>(name: string): T;
}

export interface EventTypeStrategyRegistration {
  type: EventType;
  strategy: IEventTypeStrategy;
}

export type Schedule = "monthly" | "weekly" | "daily" | "hourly";

export interface CollectorRegistration {
  create(
    config: IConfig,
    recorder: IEventRecorder,
    cache: TimeSeriesCacheWrapper,
  ): Promise<ICollector>;

  name: string;

  description: string;

  group?: string;

  schedule: Schedule;

  artifactScope: ArtifactNamespace[];

  artifactTypeScope: ArtifactType[];
}

export class Config implements IConfig {
  private storage: Record<string, any>;

  constructor() {
    this.storage = {};
  }

  get<T>(name: string): T {
    const retVal = this.storage[name];
    if (retVal === undefined || retVal === null) {
      throw new Error(`config item ${name} does not exist`);
    }
    return retVal as T;
  }
}

/**
 * Main interface to the indexer.
 */
export interface IScheduler {
  registerEventType(reg: EventTypeStrategyRegistration): void;

  registerCollector(reg: CollectorRegistration): void;

  /**
   * Should process all register collectors and schedule them
   */
  queueAll(baseTime?: DateTime): Promise<void>;

  queueJob(collector: string, baseTime: DateTime, range: Range): Promise<void>;

  runWorker(group: string): Promise<ErrorsList>;

  executeForRange(collectorName: string, range: Range): Promise<ErrorsList>;
}

/**
 * Spawns workers (this can be through any means)
 *
 * This is used by the scheduler to begin spawning workers.
 */
export interface WorkerSpawner {
  spawn(group?: string): Promise<void>;
}

export class BaseScheduler implements IScheduler {
  private recorder: IEventRecorder;
  private config: IConfig;
  private collectors: Record<string, CollectorRegistration>;
  private eventPointerManager: EventPointerManager;
  private cache: TimeSeriesCacheWrapper;
  private spawner: WorkerSpawner;
  private jobsRepository: typeof JobsRepository;
  private jobsExecutionRepository: typeof JobExecutionRepository;
  private runDir: string;

  constructor(
    runDir: string,
    recorder: IEventRecorder,
    config: IConfig,
    eventPointerManager: EventPointerManager,
    cache: TimeSeriesCacheWrapper,
    spawner: WorkerSpawner,
    jobsRepository: typeof JobsRepository,
    jobsExecutionRepository: typeof JobExecutionRepository,
  ) {
    this.runDir = runDir;
    this.recorder = recorder;
    this.config = config;
    this.collectors = {};
    this.cache = cache;
    this.eventPointerManager = eventPointerManager;
    this.spawner = spawner;
    this.jobsRepository = jobsRepository;
    this.jobsExecutionRepository = jobsExecutionRepository;
  }

  registerCollector(reg: CollectorRegistration) {
    this.collectors[reg.name] = reg;
  }

  registerEventType(reg: EventTypeStrategyRegistration) {
    this.recorder.registerEventType(reg.type, reg.strategy);
  }

  async queueAll(baseTime?: DateTime): Promise<void> {
    // Get the current time. Normalized for hour, month, day, week
    baseTime = baseTime
      ? baseTime.startOf("hour")
      : DateTime.now().toUTC().startOf("hour");
    logger.debug(`queuing jobs for ${baseTime.toISO()}`);

    const scheduleMatches: Schedule[] = ["hourly"];

    // The ranges have specific arbitrary offsets to hopefully (and cheaply)
    // ensure that data collection doesn't miss if a data source is slow.
    const scheduleRanges: Record<Schedule, Range> = {
      hourly: {
        startDate: baseTime.minus({ hour: 2 }),
        endDate: baseTime.minus({ hour: 1 }),
      },
      weekly: {
        startDate: baseTime.minus({ days: 9 }),
        endDate: baseTime.minus({ days: 2 }),
      },
      monthly: {
        startDate: baseTime.minus({ days: 3 }).startOf("month"),
        endDate: baseTime.startOf("month"),
      },
      daily: {
        startDate: baseTime.minus({ hours: 3 }).startOf("day"),
        endDate: baseTime.startOf("day"),
      },
    };

    // Find matching collector times. Offsets are intentionally set.
    const weeklyMatchDateTime = baseTime.startOf("week");
    logger.debug(`Weekly match is ${weeklyMatchDateTime.toISO()}`);
    if (weeklyMatchDateTime.equals(baseTime)) {
      scheduleMatches.push("weekly");
    }
    const dailyMatchDateTime = baseTime.startOf("day").plus({ hours: 2 });
    logger.debug(`Daily match is ${dailyMatchDateTime.toISO()}`);
    if (dailyMatchDateTime.equals(baseTime)) {
      scheduleMatches.push("daily");
    }
    const monthlyMatchDateTime = baseTime.startOf("month").plus({ days: 2 });
    logger.debug(`Monthly match is ${monthlyMatchDateTime.toISO()}`);
    if (monthlyMatchDateTime.equals(baseTime)) {
      scheduleMatches.push("monthly");
    }

    for (const name in this.collectors) {
      const collector = this.collectors[name];
      if (scheduleMatches.indexOf(collector.schedule) !== -1) {
        // attempt to schedule this job
        await this.queueJob(name, baseTime, scheduleRanges[collector.schedule]);
      }
    }
  }

  async queueJob(collectorName: string, baseTime: DateTime, range: Range) {
    const collector = this.collectors[collectorName];
    try {
      await this.jobsRepository.queueJob(
        collector.name,
        collector.group || null,
        baseTime,
        {
          startDate: range.startDate.toISO(),
          endDate: range.endDate.toISO(),
        },
      );
    } catch (err) {
      if (err instanceof JobAlreadyQueued) {
        console.log(
          `job for ${collectorName} already queued at ${baseTime.toISO()}`,
        );
        return;
      }
      throw err;
    }
  }

  async runWorker(group: string): Promise<ErrorsList> {
    // Execute from the jobs queue.
    const groups = await this.jobsRepository.availableJobGroups();

    const jobsToChoose = groups.reduce<Job[]>((jobs, grouping) => {
      if (grouping.name === "none") {
        if (group === "all" || group === "none") {
          jobs.push(...grouping.jobs);
          return jobs;
        }
      } else {
        if (grouping.name === group) {
          jobs.push(...grouping.jobs);
          return jobs;
        }
      }
      return jobs;
    }, []);

    console.log(jobsToChoose);

    if (jobsToChoose.length === 0) {
      logger.debug("no jobs available for the given group");
      return [];
    }

    const job = _.sample(jobsToChoose)!;
    const options = job.options as { startDate: string; endDate: string };
    const startDate = DateTime.fromISO(options.startDate);
    const endDate = DateTime.fromISO(options.endDate);

    if (!(startDate.isValid && endDate.isValid)) {
      throw new Error("irrecoverable error. job description is bad.");
    }

    const execution = await this.jobsExecutionRepository.createExecutionForJob(
      job,
    );
    if (!execution) {
      throw new Error("could not establish a lock");
    }
    // Write the data for the lock to disk. So that this can be used to kill any
    // prematurely killed job.
    await this.ensureRunDir();
    const lockJsonPath = this.lockJsonPath();
    await writeFile(
      lockJsonPath,
      JSON.stringify({
        execution: {
          id: execution.id,
        },
        group: group,
      }),
      { encoding: "utf-8" },
    );

    const errors = await this.executeForRange(job.collector, {
      startDate: startDate,
      endDate: endDate,
    });
    if (errors.length > 0) {
      await this.jobsExecutionRepository.updateExecutionStatus(
        execution,
        JobExecutionStatus.FAILED,
      );
    }

    try {
      await unlink(lockJsonPath);
    } catch (e) {
      logger.error("error occurred attempting to delete lock file");
    }

    // Check the available jobs after the run and spawn a worker
    const afterGroups = await this.jobsRepository.availableJobGroups();
    if (afterGroups.length) {
      // Only spawn a single worker with the same group
      if (INDEXER_SPAWN) {
        await this.spawner.spawn(group);
      } else {
        logger.debug(`No spawn allowed. would have spawned.`);
      }
    }
    return errors;
  }

  private lockJsonPath() {
    return path.join(this.runDir, "lock.json");
  }

  private async ensureRunDir() {
    return mkdirp(this.runDir);
  }

  async cleanLock() {
    // If there's an existing lock file then we need to cancel the current job and consider it failed.
    const lockJsonPath = this.lockJsonPath();
    if (!(await fileExists(lockJsonPath))) {
      logger.info("no lock found. assuming the job exited cleanly");
    }
    const lockData = await readFile(lockJsonPath, { encoding: "utf-8" });
    const lock = JSON.parse(lockData) as LockData;
    lock.execution.id;

    const r = await this.jobsExecutionRepository.updateExecutionStatusById(
      lock.execution.id,
      JobExecutionStatus.FAILED,
    );
    console.log(r);

    //await unlink(lockJsonPath);
  }

  async executeForRange(collectorName: string, range: Range) {
    logger.debug(`starting ${collectorName}`);
    const reg = this.collectors[collectorName];

    this.recorder.setActorScope(reg.artifactScope, reg.artifactTypeScope);
    const collector = await reg.create(this.config, this.recorder, this.cache);
    const errors: unknown[] = [];

    const seenIds: Record<number, number> = {};

    // Get a list of the monitored artifacts
    for await (const group of collector.groupedArtifacts()) {
      // Determine anything missing from this group
      logger.debug("determine missing artifacts");
      const missing = await this.findMissingArtifactsFromEventPointers(
        range,
        group.artifacts,
        collectorName,
      );

      // Nothing missing in this group. Skip
      if (missing.length === 0) {
        logger.debug("all artifacts already up to date");
        continue;
      }

      // Execute the collection for the missing items
      try {
        await collector.collect(
          { details: group.details, artifacts: missing },
          range,
          async (artifact) => {
            let seenCount = seenIds[artifact.id] || 0;
            seenCount += 1;
            seenIds[artifact.id] = seenCount;
            if (seenCount > 1) {
              logger.warn(`duplicate artifact commitment. skipping.`);
              return;
            }
            logger.debug(
              `completed events for "${collectorName} on Artifact[${artifact.id}]`,
            );
            return await this.eventPointerManager.commitArtifactForRange(
              range,
              artifact,
              collectorName,
            );
          },
        );
      } catch (err) {
        logger.error("Error encountered. Skipping group", err);
        errors.push(err);
        continue;
      }
      // TODO: Ensure all artifacts are committed or error
    }
    await this.recorder.waitAll();

    if (errors.length > 0) {
      logger.info("completed with errors");
    } else {
      // TODO collect errors and return here
      logger.info("completed collector run successfully");
    }
    return errors;
  }

  private async findMissingArtifactsFromEventPointers(
    range: Range,
    artifacts: Artifact[],
    collectorName: string,
  ): Promise<Artifact[]> {
    const eventPtrs =
      await this.eventPointerManager.getAllEventPointersForRange(
        range,
        artifacts,
        collectorName,
      );
    const existingMap = eventPtrs.reduce<Record<number, Range[]>>((a, c) => {
      const pointers = a[c.artifact.id] || [];
      pointers.push(rangeFromDates(c.startDate, c.endDate));
      a[c.artifact.id] = pointers;
      return a;
    }, {});
    return artifacts.filter((a) => {
      const ranges = existingMap[a.id];
      // If there're no ranges then this is missing events
      if (!ranges) {
        return true;
      }
      return (
        findMissingRanges(range.startDate, range.endDate, ranges).length > 0
      );
    });
  }
}
