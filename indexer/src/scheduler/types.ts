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
  ICommitResult,
  IEventGroupRecorder,
  IEventRecorder,
  IEventRecorderClient,
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
import { DateTime, Duration, DurationLike } from "luxon";
import _ from "lodash";
import { INDEXER_SPAWN } from "../config.js";
import { writeFile, readFile, unlink } from "fs/promises";
import path from "path";
import { fileExists } from "../utils/files.js";
import { mkdirp } from "mkdirp";
import type { Brand } from "utility-types";
import { GenericError } from "../common/errors.js";
import { UniqueArray, asyncBatchFlattened } from "../utils/array.js";
import { EventEmitter } from "node:events";
import { AsyncResults, PossiblyError } from "../utils/async-results.js";
import { assert } from "../utils/common.js";

export type IArtifactGroup<T extends object = object> = {
  name(): Promise<string>;
  meta(): Promise<T>;
  artifacts(): Promise<Artifact[]>;

  createMissingGroup(missing: Artifact[]): Promise<IArtifactGroup<T>>;
};

export type ErrorsList = PossiblyError[];

export class ArtifactCommittmentError extends GenericError {}

export interface IArtifactCommitterProducer {
  withResults(results: AsyncResults<RecordResponse>): void;
  withHandles(handles: RecordHandle[]): void;
  withNoChanges(): void;
}

export interface IArtifactCommitter extends IArtifactCommitterProducer {
  handles(): RecordHandle[];
  results(): AsyncResults<RecordResponse>;
  isComplete(): boolean;
}

class ArtifactCommitter implements IArtifactCommitter {
  private _handles: RecordHandle[];
  private _results: AsyncResults<RecordResponse>;
  private artifact: Artifact;
  private closed: boolean;

  static setup(artifact: Artifact) {
    return new ArtifactCommitter(artifact);
  }

  constructor(artifact: Artifact) {
    this.artifact = artifact;
    this._handles = [];
    this.closed = false;
    this._results = {
      success: [],
      errors: [],
    };
  }

  withHandles(handles: RecordHandle[]): void {
    if (this.closed) {
      throw new ArtifactCommittmentError(
        `committment results attempting to add unresolved handles. Artifact[id=${this.artifact.id}] committer was already resolved.`,
      );
    }
    handles.forEach((h) => {
      this._handles.push(h);
    });
  }

  withResults(results: AsyncResults<RecordResponse>): void {
    if (!this.closed) {
      this._results = results;
      this.closed = true;
    } else {
      throw new ArtifactCommittmentError(
        `committment results attempting override. Artifact[id=${this.artifact.id}] committer was already resolved.`,
      );
    }
  }

  withNoChanges(): void {
    return this.withResults({
      success: ["no changes"],
      errors: [],
    });
  }

  isComplete(): boolean {
    return this.closed;
  }

  handles(): RecordHandle[] {
    return this._handles;
  }

  results(): AsyncResults<string> {
    return this._results;
  }
}

export interface IArtifactGroupCommitmentProducer {
  commit(artifact: Artifact): IArtifactCommitterProducer;
  commitGroup(group: IEventGroupRecorder<Artifact>): void;
  failAll(err: PossiblyError): void;
}

export interface IArtifactGroupCommitmentConsumer {
  complete(result: ICommitResult): Promise<ArtifactCommitmentSummary[]>;

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

export class CollectorRegistrationError extends GenericError {}
export class CollectorDoesNotExistError extends GenericError {}

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
export interface IEventCollector {
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

export interface IPeriodicCollector {
  collect(): Promise<CollectResponse>;
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

// Collector Types. Currently there are only 2.
// - "event" - Collects events. The execution of which will be controlled by
//   `EventPointer`
// - "periodic" - This means the collector is really just a simple job that will
//   periodically execute.
export type CollectorType = "event" | "periodic";

interface CollectorRegistration {
  name: string;

  description: string;

  group?: string;

  schedule: Schedule;
}

export interface EventCollectorRegistration extends CollectorRegistration {
  create(
    config: IConfig,
    recorder: IEventRecorderClient,
    cache: TimeSeriesCacheWrapper,
  ): Promise<IEventCollector>;

  dataSetIncludesNow?: boolean;

  artifactScope: ArtifactNamespace[];

  artifactTypeScope: ArtifactType[];

  backfillInterval?: DurationLike;
}

export interface PeriodicCollectorRegistration extends CollectorRegistration {
  create(
    config: IConfig,
    cache: TimeSeriesCacheWrapper,
  ): Promise<IPeriodicCollector>;
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

export interface IExecutionSummary {
  group?: string;
  errors: PossiblyError[];
  artifactSummaries: ArtifactCommitmentSummary[];

  hasErrors(): boolean;
  successfulArtifacts(): number;
  failedArtifacts(): number;
  errorCount(): number;
}

export class ExecutionSummary implements IExecutionSummary {
  group?: string;
  errors: PossiblyError[];
  artifactSummaries: ArtifactCommitmentSummary[];

  static empty() {
    return new ExecutionSummary();
  }

  constructor() {
    this.errors = [];
    this.artifactSummaries = [];
  }

  failedArtifacts(): number {
    return this.artifactSummaries.reduce<number>((a, c) => {
      if (c.results.errors.length > 0) {
        return a + 1;
      }
      return a;
    }, 0);
  }

  successfulArtifacts(): number {
    return this.artifactSummaries.length - this.failedArtifacts();
  }

  errorCount(): number {
    const artifactErrors = this.artifactSummaries.reduce<number>((a, c) => {
      return a + c.results.errors.length;
    }, 0);
    return artifactErrors + this.errors.length;
  }

  hasErrors(): boolean {
    if (this.errors.length > 0) {
      return true;
    }
    return this.failedArtifacts() > 0;
  }
}

export interface SchedulerExecuteCollectorOptions {
  range?: Range;
  mode?: ExecutionMode;
  reindex?: boolean;
}

/**
 * Main interface to the indexer.
 */
export interface IScheduler {
  registerEventCollector(reg: EventCollectorRegistration): void;

  registerPeriodicCollector(reg: PeriodicCollectorRegistration): void;

  /**
   * Should process all register collectors and schedule them
   */
  queueAll(baseTime?: DateTime): Promise<void>;

  queueEventJob(
    collector: string,
    baseTime: DateTime,
    range: Range,
  ): Promise<void>;

  queuePeriodicJob(collector: string, baseTime: DateTime): Promise<void>;

  queueBackfill(
    collectorName: string,
    startTime: DateTime,
    backfillIntervalDays: number,
  ): Promise<void>;

  runWorker(group: string, resumeWithLock: boolean): Promise<IExecutionSummary>;

  executeCollector(
    collectorName: string,
    options?: SchedulerExecuteCollectorOptions,
  ): Promise<IExecutionSummary>;
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
    this.committers = {};
  }

  commit(artifact: Artifact): IArtifactCommitterProducer {
    return this.committerForArtifact(artifact);
  }

  private committerForArtifact(artifact: Artifact) {
    let committer = this.committers[artifact.id.valueOf()];
    if (!committer) {
      committer = ArtifactCommitter.setup(artifact);
      this.committers[artifact.id.valueOf()] = committer;
    }
    return committer;
  }

  commitGroup(group: IEventGroupRecorder<Artifact>): void {
    // Listen for errors in the group
    //const groupedHandles = group.groupedHandles()

    // Start waiting for all the artifacts asynchronously
    this.artifacts.forEach((artifact) => {
      const handles = group.handlesForGroup(artifact);
      if (handles.length === 0) {
        this.commit(artifact).withNoChanges();
      } else {
        this.commit(artifact).withHandles(handles);
      }
    });
  }

  async complete(commit: ICommitResult): Promise<ArtifactCommitmentSummary[]> {
    return await asyncBatchFlattened(this.artifacts, 1000, async (batch) => {
      return await Promise.all(
        batch.map(async (artifact) => {
          const committer = this.committers[artifact.id];
          const results = committer.isComplete()
            ? committer.results()
            : commit.collectResultsForHandles(committer.handles());
          if (results.errors.length === 0) {
            try {
              await this.eventPointerManager.commitArtifactForRange(
                this.collectorName,
                this.range,
                artifact,
              );
              logger.info(
                `successfully committed Artifact[name=${
                  artifact.name
                }, namespace=${artifact.namespace}] for ${rangeToString(
                  this.range,
                )}`,
              );
            } catch (err) {
              return {
                artifact: artifact,
                results: {
                  success: [],
                  errors: [err],
                },
              };
            }
          } else {
            logger.error(
              `cannot commit Artifact[name=${artifact.name}, namespace=${artifact.namespace}]. has ${results.errors.length} error(s)`,
            );
          }
          return {
            artifact: artifact,
            results: results,
          };
        }),
      );
    });
  }

  failAll(err: PossiblyError): void {
    this.artifacts.forEach((artifact) => {
      const committer = this.committerForArtifact(artifact);
      if (committer.isComplete()) {
        return;
      }
      committer.withResults({
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
  private eventCollectors: Record<string, EventCollectorRegistration>;
  private periodicCollectors: Record<string, PeriodicCollectorRegistration>;
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
    this.eventCollectors = {};
    this.periodicCollectors = {};
    this.eventTypes = [];
    this.cache = cache;
    this.eventPointerManager = eventPointerManager;
    this.spawner = spawner;
    this.jobsRepository = jobsRepository;
    this.jobsExecutionRepository = jobsExecutionRepository;
    this.recorderFactory = recorderFactory;
  }

  registerEventCollector(reg: EventCollectorRegistration) {
    this.assertUniqueCollectorName(reg.name);
    this.eventCollectors[reg.name] = reg;
  }

  registerPeriodicCollector(reg: PeriodicCollectorRegistration): void {
    this.assertUniqueCollectorName(reg.name);
    this.periodicCollectors[reg.name] = reg;
  }

  private assertUniqueCollectorName(name: string) {
    if (
      this.eventCollectors[name] !== undefined ||
      this.periodicCollectors[name]
    ) {
      throw new CollectorRegistrationError(
        `collector ${name} already registered. names must be unique`,
      );
    }
  }

  async newRecorder(): Promise<IEventRecorder> {
    const recorder = await this.recorderFactory();
    await recorder.setup();
    return recorder;
  }

  async queueBackfill(
    collectorName: string,
    startTime: DateTime,
    backfillIntervalDays: number,
  ): Promise<void> {
    // Only event collectors can do backfill.
    const collector = this.eventCollectors[collectorName];

    let backfillInterval: DurationLike = collector.backfillInterval
      ? collector.backfillInterval
      : { days: 30 };

    if (
      backfillIntervalDays !== 0 &&
      !(
        Duration.fromDurationLike({ days: backfillIntervalDays }) >
        Duration.fromDurationLike(backfillInterval)
      )
    ) {
      backfillInterval = { days: backfillIntervalDays };
    }

    let currentStartTime = startTime;
    let currentEndTime = currentStartTime.plus(backfillInterval);
    const baseTime = DateTime.now().toUTC().startOf("hour");

    const untilTimes: Record<Schedule, DateTime> = {
      hourly: baseTime.minus({ hour: 1 }),
      weekly: baseTime.minus({ days: 2 }),
      monthly: baseTime.startOf("month"),
      daily: baseTime.startOf("day"),
    };
    const until = untilTimes[collector.schedule];

    while (currentStartTime < until) {
      if (currentEndTime > until) {
        currentEndTime = until;
      }
      if (currentEndTime.toMillis() === currentStartTime.toMillis()) {
        break;
      }
      await this.queueEventJob(
        collectorName,
        currentStartTime,
        { startDate: currentStartTime, endDate: currentEndTime },
        true,
      );

      currentStartTime = currentStartTime.plus(backfillInterval);
      currentEndTime = currentEndTime.plus(backfillInterval);
    }
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

    for (const name in this.eventCollectors) {
      const collector = this.eventCollectors[name];
      if (scheduleMatches.indexOf(collector.schedule) !== -1) {
        // attempt to schedule this job
        await this.queueEventJob(
          name,
          baseTime,
          scheduleRanges[collector.schedule],
        );
      }
    }

    for (const name in this.periodicCollectors) {
      const collector = this.periodicCollectors[name];
      if (scheduleMatches.indexOf(collector.schedule) !== -1) {
        // attempt to schedule this job. For now we can use the same input as
        await this.queuePeriodicJob(name, baseTime);
      }
    }
  }

  async queueEventJob(
    collectorName: string,
    baseTime: DateTime,
    range: Range,
    backfill: boolean = false,
  ) {
    const options = {
      startDate: range.startDate.toISO(),
      endDate: range.endDate.toISO(),
    };
    return this.queueJob(collectorName, baseTime, backfill, options);
  }

  async queuePeriodicJob(
    collectorName: string,
    baseTime: DateTime,
  ): Promise<void> {
    return this.queueJob(collectorName, baseTime, false);
  }

  private getCollectorTypeByName(name: string): CollectorType {
    if (this.eventCollectors[name] !== undefined) {
      return "event";
    }
    if (this.periodicCollectors[name] !== undefined) {
      return "periodic";
    }
    throw new CollectorDoesNotExistError(`collector ${name} does not exist.`);
  }

  private async queueJob(
    collectorName: string,
    baseTime: DateTime,
    backfill: boolean,
    options?: Record<string, any>,
  ) {
    const collector = this.eventCollectors[collectorName];
    try {
      await this.jobsRepository.queueJob(
        collector.name,
        collector.group || null,
        baseTime,
        backfill,
        options,
      );
    } catch (err) {
      if (err instanceof JobAlreadyQueued) {
        logger.info(
          `job for ${collector.name} already queued at ${baseTime.toISO()}`,
        );
        return;
      }
      throw err;
    }
  }

  async runWorker(
    group: string,
    resumeWithLock: boolean,
  ): Promise<IExecutionSummary> {
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
        return ExecutionSummary.empty();
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

    const collectorType = this.getCollectorTypeByName(job.collector);

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

    const execSummary =
      collectorType === "event"
        ? await this.runWorkerForEventCollector(job)
        : await this.runWorkerForPeriodicCollector(job);

    let execStatus = JobExecutionStatus.FAILED;
    if (!execSummary.hasErrors()) {
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

  private async runWorkerForEventCollector(
    job: Job,
  ): Promise<IExecutionSummary> {
    const options = job.options as { startDate: string; endDate: string };
    const startDate = DateTime.fromISO(options.startDate);
    const endDate = DateTime.fromISO(options.endDate);

    if (!(startDate.isValid && endDate.isValid)) {
      throw new Error("irrecoverable error. job description is bad.");
    }

    return await this.executeCollector(job.collector, {
      range: {
        startDate: startDate,
        endDate: endDate,
      },
      mode: "all-at-once",
    });
  }

  private async runWorkerForPeriodicCollector(
    job: Job,
  ): Promise<IExecutionSummary> {
    return await this.executeCollector(job.collector);
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
    options?: SchedulerExecuteCollectorOptions,
  ) {
    const collectorType = this.getCollectorTypeByName(collectorName);
    let executionSummary: IExecutionSummary;

    if (collectorType === "event") {
      assert(options?.range !== undefined, "Range must be set");
      assert(options?.mode !== undefined, "Mode must be set");
      executionSummary = await this.executeEventCollector(
        collectorName,
        options.range,
        options.mode,
        options.reindex || false,
      );
    } else if (collectorType === "periodic") {
      executionSummary = await this.executePeriodicCollector(collectorName);
    } else {
      throw new Error("collector type unknown. cannot execute collector");
    }

    return executionSummary;
  }

  async executePeriodicCollector(collectorName: string) {
    const reg = this.periodicCollectors[collectorName];
    const collector = await reg.create(this.config, this.cache);

    const summary = ExecutionSummary.empty();
    try {
      const res = await collector.collect();
      if (res) {
        summary.errors.push(...res.errors);
      }
    } catch (err) {
      summary.errors.push(err);
    }

    return summary;
  }

  async executeEventCollector(
    collectorName: string,
    range: Range,
    mode: ExecutionMode = "all-at-once",
    reindex: boolean = false,
  ) {
    if (range.startDate >= range.endDate) {
      throw new Error(`invalid input range ${rangeToString(range)}`);
    }
    logger.debug(
      `starting ${collectorName} in ${mode} for range ${rangeToString(range)}`,
    );
    const reg = this.eventCollectors[collectorName];
    if (mode === "all-at-once") {
      return this.executeForRange(reg, range, reindex);
    } else {
      // Execute range by day
      const ranges = rangeSplit(range, "day");

      const summaries: IExecutionSummary[] = [];
      for (const pullRange of ranges) {
        const result = await this.executeForRange(reg, pullRange, reindex);
        summaries.push(result);
      }
      const summary = summaries.reduce<ExecutionSummary>((acc, curr) => {
        acc.errors.push(...curr.errors);
        acc.artifactSummaries.push(...curr.artifactSummaries);
        return acc;
      }, ExecutionSummary.empty());
      return summary;
    }
  }

  async executeForRange(
    collectorReg: EventCollectorRegistration,
    range: Range,
    reindex: boolean,
  ) {
    const recorder = await this.newRecorder();
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

    const executionSummary = ExecutionSummary.empty();

    recorder.addListener("error", (err) => {
      logger.error("caught error on the recorder");
      logger.error(err);
      executionSummary.errors.push(err);
    });

    const collector = await collectorReg.create(
      this.config,
      recorder,
      this.cache,
    );

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
    if (reindex) {
      logger.info(
        `-------------------------REINDEXING---------------------------`,
      );
    }

    // Get a list of the monitored artifacts
    for await (const group of collector.groupedArtifacts()) {
      const artifacts = await group.artifacts();
      artifacts.forEach(({ id }) => expectedArtifacts.push(id));

      // Determine anything missing from this group
      const groupName = await group.name();
      const missing = reindex
        ? artifacts
        : await this.findMissingArtifactsFromEventPointers(
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
        // Start the recorder
        await recorder.begin();

        const response = await collector.collect(
          await group.createMissingGroup(missing),
          range,
          committer,
        );

        // This is jank and needs to be fixed. This can be cleaned up.
        const commitResult = await recorder.commit();
        logger.debug(`${groupName}: waiting for artifacts to complete commits`);

        const artifactSummaries = await committer.complete(commitResult);
        logger.debug(`completed commits for ${artifactSummaries.length}`);
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
        await recorder.rollback();
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

    if (executionSummary.hasErrors()) {
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
