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
import { INDEXER_NO_SPAWN } from "../config.js";

export type ArtifactGroup = {
  details: unknown;
  artifacts: Artifact[];
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
  schedule(): Promise<void>;

  runWorker(group: string): Promise<void>;

  executeForRange(collectorName: string, range: Range): Promise<void>;
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

  constructor(
    recorder: IEventRecorder,
    config: IConfig,
    eventPointerManager: EventPointerManager,
    cache: TimeSeriesCacheWrapper,
    spawner: WorkerSpawner,
    jobsRepository: typeof JobsRepository,
    jobsExecutionRepository: typeof JobExecutionRepository,
  ) {
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

  async schedule(): Promise<void> {
    // Get the current time. Normalized for hour, month, day, week
    const now = DateTime.now().toUTC().startOf("hour");

    const scheduleMatches: Schedule[] = ["hourly"];
    const scheduleRanges: Record<Schedule, Range> = {
      hourly: {
        startDate: now.minus({ hour: 2 }),
        endDate: now.minus({ hour: 1 }),
      },
      weekly: {
        startDate: now.minus({ days: 9 }),
        endDate: now.minus({ days: 2 }),
      },
      monthly: {
        startDate: now.minus({ days: 3 }).startOf("month"),
        endDate: now.startOf("month"),
      },
      daily: {
        startDate: now.minus({ hours: 3 }).startOf("day"),
        endDate: now.startOf("day"),
      },
    };

    // Find matching collector times
    if (now.startOf("week").equals(now)) {
      scheduleMatches.push("weekly");
    }
    if (now.startOf("day").plus({ hours: 2 }).equals(now)) {
      scheduleMatches.push("daily");
    }
    if (now.startOf("month").plus({ days: 2 }).equals(now)) {
      scheduleMatches.push("monthly");
    }

    for (const name in this.collectors) {
      const collector = this.collectors[name];
      if (scheduleMatches.indexOf(collector.schedule) !== -1) {
        // attempt to schedule this job
        const range = scheduleRanges[collector.schedule];
        try {
          await this.jobsRepository.queueJob(
            collector.name,
            collector.group || null,
            now,
            {
              startDate: range.startDate.toISO(),
              endDate: range.endDate.toISO(),
            },
          );
        } catch (err) {
          if (err instanceof JobAlreadyQueued) {
            continue;
          }
          throw err;
        }
      }
    }
  }

  async runWorker(group: string): Promise<void> {
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

    if (jobsToChoose.length === 0) {
      logger.debug("no jobs queued for the given group");
      return;
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
    try {
      await this.executeForRange(job.collector, {
        startDate: startDate,
        endDate: endDate,
      });
    } catch (err) {
      this.jobsExecutionRepository.updateExecutionStatus(
        execution,
        JobExecutionStatus.FAILED,
      );
    }
    // Check the available jobs after the run and spawn a worker
    const afterGroups = await this.jobsRepository.availableJobGroups();
    if (afterGroups.length) {
      // Only spawn a single worker with the same group
      if (INDEXER_NO_SPAWN) {
        await this.spawner.spawn(group);
      } else {
        logger.debug(`No spawn allowed. would have spawned.`);
      }
    }
    return;
  }

  async executeForRange(collectorName: string, range: Range) {
    logger.debug(`starting ${collectorName}`);
    const reg = this.collectors[collectorName];

    this.recorder.setActorScope(reg.artifactScope, reg.artifactTypeScope);
    const collector = await reg.create(this.config, this.recorder, this.cache);

    // Get a list of the monitored artifacts
    for await (const group of collector.groupedArtifacts()) {
      // Determine anything missing from this group
      const missing = await this.findMissingArtifactsFromEventPointers(
        range,
        group.artifacts,
        collectorName,
      );

      // Nothing missing in this group. Skip
      if (missing.length === 0) {
        continue;
      }

      // Execute the collection for the missing items
      try {
        await collector.collect(
          { details: group.details, artifacts: missing },
          range,
          async (artifact) => {
            await this.eventPointerManager.commitArtifactForRange(
              range,
              artifact,
              collectorName,
            );
          },
        );
      } catch (err) {
        logger.error("Error encountered. Skipping group", err);
        continue;
      }
      // TODO: Ensure all artifacts are committed or error
    }
    await this.recorder.waitAll();
    // TODO collect errors and return here
    logger.info("completed collector run successfully");
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
