import {
  Artifact,
  ArtifactNamespace,
  ArtifactType,
  EventType,
  Job,
  JobExecution,
  JobExecutionStatus,
} from "../db/orm-entities.js";
import {
  IEventGroupRecorder,
  IEventRecorder,
  IEventTypeStrategy,
  RecordHandle,
  RecordResponse,
  RecorderFactory,
} from "../recorder/types.js";
import {
  Range,
  findMissingRanges,
  rangeFromDates,
  rangeSplit,
  rangeToString,
} from "../utils/ranges.js";
import { IEventPointerManager } from "./pointers.js";
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
import type { Brand } from "utility-types";
import { GenericError } from "../common/errors.js";
import { UniqueArray } from "../utils/array.js";
import { EventEmitter } from "node:events";
import {
  AsyncResults,
  PossiblyError,
  collectAsyncResults,
} from "../utils/async-results.js";

export type IArtifactGroup<T extends object = object> = {
  name(): Promise<string>;
  meta(): Promise<T>;
  artifacts(): Promise<Artifact[]>;

  createMissingGroup(missing: Artifact[]): Promise<IArtifactGroup<T>>;
};

export type ErrorsList = PossiblyError[];

type ArtifactCommitterFn = (results: AsyncResults<RecordResponse>) => void;

export interface IArtifactCommitter {
  withResults(results: AsyncResults<RecordResponse>): void;
  withHandles(handles: RecordHandle[]): void;
  withNoChanges(): void;
}

class ArtifactCommitter implements IArtifactCommitter {
  private cb: ArtifactCommitterFn;

  static setup(cb: ArtifactCommitterFn) {
    return new ArtifactCommitter(cb);
  }

  constructor(cb: ArtifactCommitterFn) {
    this.cb = cb;
  }

  withHandles(handles: RecordHandle[]): void {
    const handlesAsPromises = handles.map((h) => h.wait());
    collectAsyncResults(handlesAsPromises)
      .then((results) => {
        this.withResults(results);
      })
      .catch((err) => {
        logger.error("FATAL: unexpected error. this is being suppressed", err);
      });
  }

  withResults(results: AsyncResults<string>): void {
    return this.cb(results);
  }

  withNoChanges(): void {
    return this.withResults({
      success: ["no changes"],
      errors: [],
    });
  }
}

export interface IArtifactGroupCommitmentProducer {
  commit(artifact: Artifact): IArtifactCommitter;
  commitGroup(group: IEventGroupRecorder<Artifact>): void;
  failAll(err: PossiblyError): void;
}

export interface IArtifactGroupCommitmentConsumer {
  waitAll(): Promise<ArtifactCommitmentSummary[]>;
  failAll(err: PossiblyError): void;

  addListener(listener: "error", cb: (err: unknown) => void): EventEmitter;
  removeListener(listener: "error", cb: (err: unknown) => void): EventEmitter;
}

export type ArtifactRecordingStatus = {
  recordings: RecordResponse[];
  errors: PossiblyError[];
};

export type CollectorErrorsOptions = {
  unsortedErrors?: ErrorsList;
  errorsBySourceId?: Record<string, ErrorsList>;
};

export class CollectorErrors extends GenericError {
  constructor(message: string, options?: CollectorErrorsOptions) {
    const details = {
      ...options,
    };
    super(message, details);
  }
}

type LockData = {
  execution: {
    id: number;
  };
  group: string;
};

export type CommitArtifactCallback = (
  artifact: Artifact | Artifact[],
) => Promise<void>;

/**
 * The interface for the scheduler that manages all of the schedules for jobs
 */
export interface ICollector {
  // Yield arrays of artifacts that this collector monitors. This is an async
  // generator so that artifacts can be yielded in groups if needed.
  groupedArtifacts(): AsyncGenerator<IArtifactGroup<object>>;

  allArtifacts(): Promise<Artifact[]>;

  collect(
    group: IArtifactGroup<object>,
    range: Range,
    committer: IArtifactGroupCommitmentProducer,
  ): Promise<CollectResponse>;
}

export interface Errors {
  errors: unknown[];
}

export type CollectResponse = Errors | void;

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
export type ExecutionMode = "all-at-once" | "progressive";

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

  dataSetIncludesNow?: boolean;

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

export interface ExecutionSummary {
  group?: string;
  errors: PossiblyError[];
  artifactSummaries: ArtifactCommitmentSummary[];
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

  runWorker(group: string, resumeWithLock: boolean): Promise<ExecutionSummary>;

  executeCollector(
    collectorName: string,
    range: Range,
    mode: ExecutionMode,
  ): Promise<ExecutionSummary>;
}

export type ArtifactCommitmentSummary = {
  results: AsyncResults<string>;
  artifact: Artifact;
};

export class ArtifactRecordsCommitmentWrapper
  implements IArtifactGroupCommitmentProducer, IArtifactGroupCommitmentConsumer
{
  private collectorName: string;
  private range: Range;
  private promises: Promise<ArtifactCommitmentSummary>[];
  private committers: Record<number, IArtifactCommitter>;
  private artifacts: Artifact[];
  private emitter: EventEmitter;
  private eventPointerManager: IEventPointerManager;
  private duplicatesTracker: Record<number, number>;
  private recorder: IEventRecorder;

  static setup(
    collectorName: string,
    range: Range,
    eventPointerManager: IEventPointerManager,
    artifacts: Artifact[],
    duplicatesTracker: Record<number, number>,
  ) {
    const wrapper = new ArtifactRecordsCommitmentWrapper(
      collectorName,
      range,
      eventPointerManager,
      artifacts,
      duplicatesTracker,
    );
    wrapper.createPromises();
    wrapper.createCommitters();
    return wrapper;
  }

  private constructor(
    collectorName: string,
    range: Range,
    eventPointerManager: IEventPointerManager,
    artifacts: Artifact[],
    duplicatesTracker: Record<number, number>,
  ) {
    this.collectorName = collectorName;
    this.range = range;
    this.eventPointerManager = eventPointerManager;
    this.artifacts = artifacts;
    this.emitter = new EventEmitter();
    this.promises = [];
    this.duplicatesTracker = duplicatesTracker;
  }

  private createPromises() {
    this.promises = this.artifacts.map((artifact) => {
      return new Promise<ArtifactCommitmentSummary>((resolve) => {
        this.emitter.addListener(
          `${artifact.id}`,
          (results: AsyncResults<RecordResponse>) => {
            const internal = async () => {
              if (results.errors.length > 0) {
                return resolve({
                  artifact: artifact,
                  results: results,
                });
              }
              const commitmentErrors: PossiblyError[] = [];

              let seenCount = this.duplicatesTracker[artifact.id] || 0;

              if (seenCount === 0) {
                try {
                  await this.eventPointerManager.commitArtifactForRange(
                    this.collectorName,
                    this.range,
                    artifact,
                  );
                  seenCount += 1;
                  this.duplicatesTracker[artifact.id] = seenCount;
                  logger.info(
                    `completed events for "${this.collectorName} on Artifact[${
                      artifact.id
                    }] for ${rangeToString(this.range)}`,
                  );
                } catch (err) {
                  commitmentErrors.push(err);
                }
              } else {
                logger.warn(
                  `duplicate artifact commitment for Artifact[name=${artifact.name}, namespace=${artifact.namespace}]. skipping`,
                );
              }
              resolve({
                artifact: artifact,
                results: results,
              });
            };

            internal().catch((err) => {
              logger.error(
                "FATAL: unexpected error caught during artifact committment",
                err,
              );
              this.emitter.emit("error", err);
            });
          },
        );
      });
    });
  }

  private createCommitters() {
    this.committers = this.artifacts.reduce<Record<string, IArtifactCommitter>>(
      (acc, artifact) => {
        acc[artifact.id.valueOf()] = ArtifactCommitter.setup((results) => {
          this.emitter.emit(`${artifact.id}`, results);
        });
        return acc;
      },
      {},
    );
  }

  commit(artifact: Artifact): IArtifactCommitter {
    return this.getCommitter(artifact);
  }

  commitGroup(group: IEventGroupRecorder<Artifact>): void {
    // Listen for errors in the group
    const errorListener = (err: unknown) => {
      logger.error("caught error committing a group");
      this.emitter.emit("error", err);
    };
    group.addListener("error", errorListener);

    // Start waiting for all the artifacts asynchronously
    this.artifacts.map((artifact) => {
      return group
        .wait(artifact)
        .then((results) => {
          group.removeListener("error", errorListener);
          this.commit(artifact).withResults(results);
        })
        .catch((err) => {
          logger.error(
            "FATAL: unexpected error handling artifact commitment",
            err,
          );
        });
    });
    // Notify the group recorder that we're committing
    group.commit();
  }

  async waitAll(): Promise<ArtifactCommitmentSummary[]> {
    return await Promise.all(this.promises);
  }

  failAll(err: PossiblyError): void {
    this.artifacts.forEach((artifact) => {
      this.commit(artifact).withResults({
        errors: [err],
        success: [],
      });
    });
  }

  successAll(results: AsyncResults<RecordResponse>): void {
    this.artifacts.forEach((artifact) => {
      this.commit(artifact).withResults(results);
    });
  }

  private getCommitter(artifact: Artifact) {
    const committer = this.committers[artifact.id];
    if (!committer) {
      throw new Error(
        `unexpected Artifact[name=${artifact.name}, namespace=${artifact.namespace}]`,
      );
    }
    return committer;
  }

  addListener(listener: "error", cb: (err: unknown) => void): EventEmitter {
    return this.emitter.addListener(listener, cb);
  }

  removeListener(listener: "error", cb: (err: unknown) => void): EventEmitter {
    return this.emitter.removeListener(listener, cb);
  }
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
  private config: IConfig;
  private collectors: Record<string, CollectorRegistration>;
  private eventPointerManager: IEventPointerManager;
  private recorderFactory: RecorderFactory;
  private cache: TimeSeriesCacheWrapper;
  private spawner: WorkerSpawner;
  private jobsRepository: typeof JobsRepository;
  private jobsExecutionRepository: typeof JobExecutionRepository;
  private runDir: string;
  private eventTypes: EventTypeStrategyRegistration[];

  constructor(
    runDir: string,
    recorderFactory: RecorderFactory,
    config: IConfig,
    eventPointerManager: IEventPointerManager,
    cache: TimeSeriesCacheWrapper,
    spawner: WorkerSpawner,
    jobsRepository: typeof JobsRepository,
    jobsExecutionRepository: typeof JobExecutionRepository,
  ) {
    this.runDir = runDir;
    this.config = config;
    this.collectors = {};
    this.eventTypes = [];
    this.cache = cache;
    this.eventPointerManager = eventPointerManager;
    this.spawner = spawner;
    this.jobsRepository = jobsRepository;
    this.jobsExecutionRepository = jobsExecutionRepository;
    this.recorderFactory = recorderFactory;
  }

  registerCollector(reg: CollectorRegistration) {
    this.collectors[reg.name] = reg;
  }

  registerEventType(reg: EventTypeStrategyRegistration) {
    this.eventTypes.push(reg);
  }

  newRecorder(): IEventRecorder {
    const recorder = this.recorderFactory();
    this.eventTypes.forEach((r) => {
      recorder.registerEventType(r.strategy);
    });
    return recorder;
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
        logger.info(
          `job for ${collectorName} already queued at ${baseTime.toISO()}`,
        );
        return;
      }
      throw err;
    }
  }

  async runWorker(
    group: string,
    resumeWithLock: boolean,
  ): Promise<ExecutionSummary> {
    let job: Job;
    let execution: JobExecution | undefined;

    // Execute from the jobs queue.
    if (resumeWithLock && (await this.lockExists())) {
      logger.info(`resuming with job lock at ${this.lockJsonPath()}`);

      const lock = await this.loadLock();
      execution = await this.jobsExecutionRepository.findOneOrFail({
        relations: {
          job: true,
        },
        where: {
          id: lock.execution.id as Brand<number, "JobExecutionId">,
        },
      });
      job = execution.job;
    } else {
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
        logger.debug("no jobs available for the given group");
        return {
          errors: [],
          artifactSummaries: [],
        };
      }

      job = _.sample(jobsToChoose)!;
      execution = await this.jobsExecutionRepository.createExecutionForJob(job);

      if (!execution) {
        throw new Error("could not establish a lock");
      }
    }
    if (!execution) {
      throw new Error("unexpected error. execution not set");
    }

    const options = job.options as { startDate: string; endDate: string };
    const startDate = DateTime.fromISO(options.startDate);
    const endDate = DateTime.fromISO(options.endDate);

    if (!(startDate.isValid && endDate.isValid)) {
      throw new Error("irrecoverable error. job description is bad.");
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

    const execSummary = await this.executeCollector(
      job.collector,
      {
        startDate: startDate,
        endDate: endDate,
      },
      "all-at-once",
    );

    let execStatus = JobExecutionStatus.FAILED;
    if (execSummary.errors.length === 0) {
      execStatus = JobExecutionStatus.COMPLETE;
    }
    await this.jobsExecutionRepository.updateExecutionStatus(
      execution,
      execStatus,
    );

    // Check the available jobs after the run and spawn a worker
    logger.info("releasing lock for current worker");
    const afterGroups = await this.jobsRepository.availableJobGroups();
    if (afterGroups.length) {
      // Only spawn a single worker with the same group
      if (INDEXER_SPAWN) {
        await this.spawner.spawn(group);
      } else {
        logger.debug(`No spawn allowed. would have spawned.`);
      }
    }

    try {
      logger.info("deleting jobs lock file");
      await unlink(lockJsonPath);
    } catch (e) {
      logger.error("error occurred attempting to delete lock file");
    }
    return execSummary;
  }

  private lockJsonPath() {
    return path.join(this.runDir, "lock.json");
  }

  private async ensureRunDir() {
    return mkdirp(this.runDir);
  }

  private async lockExists(): Promise<boolean> {
    return await fileExists(this.lockJsonPath());
  }

  private async loadLock() {
    const lockData = await readFile(this.lockJsonPath(), { encoding: "utf-8" });
    return JSON.parse(lockData) as LockData;
  }

  async cleanLock() {
    // If there's an existing lock file then we need to cancel the current job and consider it failed.
    const lockJsonPath = this.lockJsonPath();
    if (!(await fileExists(lockJsonPath))) {
      logger.info("no lock found. assuming the job exited cleanly");
      return;
    }
    const lock = await this.loadLock();

    await this.jobsExecutionRepository.updateExecutionStatusById(
      lock.execution.id,
      JobExecutionStatus.FAILED,
    );
    await unlink(lockJsonPath);
  }

  async executeCollector(
    collectorName: string,
    range: Range,
    mode: ExecutionMode = "all-at-once",
  ) {
    if (range.startDate >= range.endDate) {
      throw new Error(`invalid input range ${rangeToString(range)}`);
    }
    logger.debug(`starting ${collectorName} in ${mode}`);
    const reg = this.collectors[collectorName];
    if (mode === "all-at-once") {
      return this.executeForRange(reg, range);
    } else {
      // Execute range by day
      const ranges = rangeSplit(range, "day");

      const summaries: ExecutionSummary[] = [];
      for (const pullRange of ranges) {
        const result = await this.executeForRange(reg, pullRange);
        summaries.push(result);
      }
      const summary = summaries.reduce<ExecutionSummary>(
        (acc, curr) => {
          acc.errors.push(...curr.errors);
          acc.artifactSummaries.push(...curr.artifactSummaries);
          return acc;
        },
        {
          errors: [],
          artifactSummaries: [],
        },
      );
      return summary;
    }
  }

  async executeForRange(collectorReg: CollectorRegistration, range: Range) {
    const recorder = this.newRecorder();
    recorder.setActorScope(
      collectorReg.artifactScope,
      collectorReg.artifactTypeScope,
    );
    if (collectorReg.dataSetIncludesNow) {
      recorder.setRange({
        startDate: range.startDate,
        endDate: DateTime.now().toUTC(),
      });
    } else {
      recorder.setRange(range);
    }
    const collector = await collectorReg.create(
      this.config,
      recorder,
      this.cache,
    );
    const executionSummary: ExecutionSummary = {
      artifactSummaries: [],
      errors: [],
    };

    recorder.addListener("error", (err) => {
      logger.error("caught error on the recorder");
      logger.error(err);
      executionSummary.errors.push(err);
    });

    const seenIds: Record<number, number> = {};

    const expectedArtifacts = new UniqueArray((a: number) => a);

    // Get a full count of the remaining work so we can provide a percentage of completion.
    const artifacts = await collector.allArtifacts();
    const allMissing = await this.findMissingArtifactsFromEventPointers(
      range,
      artifacts,
      collectorReg.name,
    );
    let totalMissing = allMissing.length;
    logger.info(
      `--------------------------------------------------------------`,
    );
    logger.info("Collection summary:");
    logger.info(`    Total items: ${artifacts.length}`);
    logger.info(`    Missing items: ${allMissing.length}`);
    logger.info(
      `--------------------------------------------------------------`,
    );

    // Get a list of the monitored artifacts
    for await (const group of collector.groupedArtifacts()) {
      const artifacts = await group.artifacts();
      artifacts.forEach(({ id }) => expectedArtifacts.push(id));

      // Determine anything missing from this group
      const groupName = await group.name();
      const missing = await this.findMissingArtifactsFromEventPointers(
        range,
        artifacts,
        collectorReg.name,
      );

      const committer = ArtifactRecordsCommitmentWrapper.setup(
        collectorReg.name,
        range,
        this.eventPointerManager,
        missing,
        seenIds,
      );

      // Listen for errors on the committer
      const committerErrorListener = (err: unknown) => {
        logger.error("caught error on the committer");
        logger.error(err);
        executionSummary.errors.push(err);
      };
      committer.addListener("error", committerErrorListener);

      // Nothing missing in this group. Skip
      if (missing.length === 0) {
        logger.debug(`${groupName}: all artifacts already up to date`);
        continue;
      }
      logger.debug(
        `${groupName}: missing ${missing.length} artifacts for the group. ${totalMissing} remaining`,
      );

      // Execute the collection for the missing items
      try {
        const response = await collector.collect(
          await group.createMissingGroup(missing),
          range,
          committer,
        );
        logger.debug(`${groupName}: waiting for artifacts to complete commits`);

        const artifactSummaries = await committer.waitAll();
        totalMissing = totalMissing - artifactSummaries.length;
        executionSummary.artifactSummaries.push(...artifactSummaries);

        if (response) {
          const errorsResponse = response as Errors;
          if (errorsResponse.errors) {
            executionSummary.errors.push(...errorsResponse.errors);
          }
        }
      } catch (err) {
        logger.error("Error encountered. Skipping group", err);
        committer.failAll(err);
        executionSummary.errors.push(err);
        continue;
      }
      committer.removeListener("error", committerErrorListener);
    }

    logger.debug("collection recorded but waiting for recorder");

    try {
      await recorder.close();
    } catch (err) {
      logger.error("error while waiting for the recorder to complete", err);
      executionSummary.errors.push(err);
    }

    if (executionSummary.errors.length > 0) {
      logger.info("completed with errors");
    } else {
      // TODO collect errors and return here
      logger.info(
        `completed collector run successfully for ${expectedArtifacts.length} artifacts.`,
      );
    }
    return executionSummary;
  }

  private async findMissingArtifactsFromEventPointers(
    range: Range,
    artifacts: Artifact[],
    collectorName: string,
  ): Promise<Artifact[]> {
    const eventPtrs =
      await this.eventPointerManager.getAllEventPointersForRange(
        collectorName,
        range,
        artifacts,
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
