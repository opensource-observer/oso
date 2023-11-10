import {
  ArtifactNamespace,
  ArtifactType,
  Event,
  EventType,
  RecorderTempEvent,
  Recording,
} from "../db/orm-entities.js";
import {
  IEventRecorder,
  IncompleteEvent,
  IEventTypeStrategy,
  IncompleteArtifact,
  RecorderError,
  EventRecorderOptions,
  RecordHandle,
  IRecorderEvent,
  IRecorderEventType,
  CommitResult as IRecorderCommitResult,
} from "./types.js";
import { Repository } from "typeorm";
import { UniqueArray } from "../utils/array.js";
import { logger } from "../utils/logger.js";
import _ from "lodash";
import { Range, isWithinRange } from "../utils/ranges.js";
import { EventEmitter } from "node:events";
import { randomUUID } from "node:crypto";
import { DateTime } from "luxon";
import { RecordResponse } from "./types.js";
import { AsyncResults } from "../utils/async-results.js";
import { ensure, ensureNumber, ensureString } from "../utils/common.js";
import { setTimeout as asyncTimeout } from "node:timers/promises";
import { DataSource } from "typeorm/browser";
import { timer } from "../utils/debug.js";

export interface BatchEventRecorderOptions {
  maxBatchSize: number;
  timeoutMs: number;
  flushIntervalMs: number;
  tempTableExpirationDays: number;
  flusher?: IFlusher;
}

const defaultBatchEventRecorderOptions: BatchEventRecorderOptions = {
  maxBatchSize: 100000,

  // 15 minute timeout seems sane for completing any db writes (in a normal
  // case). When backfilling this should be made much bigger.
  timeoutMs: 900000,

  flushIntervalMs: 2000,

  tempTableExpirationDays: 1,
};

export type FlusherCallback = () => Promise<void>;

export interface IFlusher {
  notify(size: number): void;
  clear(): void;
  onFlush(cb: FlusherCallback): void;
}

/**
 * A flusher that accumulates some arbitrary size (assumed to be the batch size)
 * and chooses to flush once that size is reached or a timeout has been met.
 */
export class TimeoutBatchedFlusher implements IFlusher {
  private timeout: NodeJS.Timeout | null;
  private timeoutMs: number;
  private waitMs: number;
  private size: number;
  private cb: FlusherCallback | undefined;
  private maxSize: number;
  private triggered: boolean;
  private nextFlush: DateTime;
  private stopped: boolean;

  constructor(timeoutMs: number, maxSize: number) {
    if (timeoutMs < 100) {
      throw new Error("timeout is too short");
    }
    this.timeoutMs = timeoutMs;
    this.waitMs = timeoutMs;
    this.timeout = null;
    this.size = 0;
    this.maxSize = maxSize;
    this.triggered = false;
    this.stopped = false;
    this.setNextFlush();
  }

  private setNextFlush() {
    this.nextFlush = DateTime.now().plus({ milliseconds: this.timeoutMs });
  }

  notify(size: number): void {
    if (this.triggered) {
      return;
    }
    this.size += size;

    // if the size is 0 then this was called without anything in the queue. That
    // means we should slow down processing the queue.
    if (this.size == 0) {
      if (this.waitMs == 0) {
        this.waitMs = this.timeoutMs / 2;
      }
      this.waitMs += this.waitMs;
    } else {
      this.waitMs = this.timeoutMs;
    }

    // We should allow the flush notification to get pushed while the size of
    // the flush is small.
    if (this.size < this.maxSize) {
      this.resetTimeout();
    }
  }

  private resetTimeout() {
    if (this.stopped) {
      if (this.timeout) {
        clearTimeout(this.timeout);
      }
    }
    // Only reset the timeout if the flusher is currently untriggered. A
    // triggered state means that this flusher is executing the callback
    if (!this.triggered) {
      if (this.timeout) {
        clearTimeout(this.timeout);
      }

      this.timeout = setTimeout(() => {
        // It is expected that the consuming class will clear the flusher.
        this.triggered = true;

        if (this.cb) {
          this.cb()
            .then(() => {
              this.triggered = false;
              // Reset size which is just a count of notifications This allows the
              // timeout to backoff if the notify function is continously called and
              // this.size remains 0
              this.size = 0;
              this.setNextFlush();
              this.notify(0);
            })
            .catch((err) => {
              // This should not happen and will trigger a failure. It is
              // expected that the callback will capture all errors.
              logger.error("recorder is not catching some errors");
              logger.error(err);

              // This will cause an uncaughtException error to be thrown and the
              // entire application to stop.
              throw err;
            });
        }
      }, this.waitMs);
    }
  }

  onFlush(cb: FlusherCallback): void {
    if (this.timeout) {
      clearTimeout(this.timeout);
    }
    this.cb = cb;
  }

  clear(): void {
    this.size = 0;
    this.waitMs = 0;
    if (this.timeout) {
      clearTimeout(this.timeout);
    }
    this.timeout = null;
    this.triggered = false;
  }
}

function eventUniqueId(
  event: Pick<IRecorderEvent, "sourceId" | "type">,
): string {
  return `${event.type}:${event.sourceId}`;
}

export class RecorderEventType implements IRecorderEventType {
  private _name: string;
  private _version: number;

  constructor(name: string, version: number) {
    this._name = name;
    this._version = version;
  }

  static fromDBEventType(eventType: EventType) {
    return new RecorderEventType(eventType.name, eventType.version);
  }

  get name(): string {
    return this._name;
  }
  get version(): number {
    return this._version;
  }

  toString() {
    return `${this.name}:v${this.version}`;
  }
}

export class RecorderEvent implements IRecorderEvent {
  private _id: number | null;
  private _time: DateTime;
  private _type: { name: string; version: number };
  private _sourceId: string;
  private _to: IncompleteArtifact;
  private _from: IncompleteArtifact | null | undefined;
  private _amount: number;
  private _details: object;

  private constructor(
    id: number | null,
    time: DateTime,
    type: IRecorderEventType,
    sourceId: string,
    to: IncompleteArtifact,
    from: IncompleteArtifact | null | undefined,
    amount: number,
    details?: object,
  ) {
    this._id = id;
    this._time = time;
    this._type = type;
    this._sourceId = sourceId;
    this._to = to;
    this._from = from;
    this._amount = amount;
    this._details = details || {};
  }

  static fromIncompleteEvent(event: IncompleteEvent) {
    const e = new RecorderEvent(
      null,
      event.time,
      event.type,
      event.sourceId,
      event.to,
      event.from,
      event.amount,
      event.details,
    );
    try {
      e.ensureIsValid();
    } catch (err) {
      logger.debug(`errors converting IncompleteEvent to a RecorderEvent`);
      logger.error(err);
      throw err;
    }
    return e;
  }

  static fromDBEvent(event: Event) {
    return new RecorderEvent(
      event.id,
      DateTime.fromJSDate(event.time),
      event.type,
      event.sourceId,
      event.to,
      event.from,
      event.amount,
      event.details,
    );
  }

  get id(): number | null {
    return this._id;
  }

  get time(): DateTime {
    return this._time;
  }

  get type(): IRecorderEventType {
    const type = this._type;
    return {
      get name(): string {
        return type.name;
      },
      get version(): number {
        return type.version;
      },
      toString() {
        return `${type.name}:v${type.version}`;
      },
    };
  }

  get sourceId(): string {
    return this._sourceId;
  }

  get to(): IncompleteArtifact {
    return {
      name: this._to.name,
      namespace: this._to.namespace,
      type: this._to.type,
    };
  }

  get from(): IncompleteArtifact | null {
    if (!this._from) {
      return null;
    }
    return {
      name: this._from.name,
      namespace: this._from.namespace,
      type: this._from.type,
    };
  }

  get amount(): number {
    return this._amount;
  }

  get details(): object {
    return this._details;
  }

  ensureIsValid() {
    ensureNumber(this._amount);
    ensureString(this._sourceId);
    ensure<IncompleteArtifact>(this._to, "artifact for `to` must be defined");
    if (!this._time.isValid) {
      throw new Error("record date is invalid");
    }
    if (this._sourceId === "") {
      throw new Error("sourceId cannot be empty");
    }
  }
}

type OrNull<T> = T | null;

interface PGRecorderTempEventBatchInput {
  recorderIds: string[];
  batchIds: number[];
  sourceIds: string[];
  typeIds: number[];
  times: Date[];
  toNames: string[];
  toNamespaces: string[];
  toTypes: string[];
  toUrls: OrNull<string>[];
  fromNames: OrNull<string>[];
  fromNamespaces: OrNull<ArtifactNamespace>[];
  fromTypes: OrNull<ArtifactType>[];
  fromUrls: OrNull<string>[];
  amounts: number[];
  details: Record<string, any>[];
}

export type RecorderEventRef = Pick<IRecorderEvent, "sourceId" | "type">;

export class BatchEventRecorder implements IEventRecorder {
  private eventTypeStrategies: Record<string, IEventTypeStrategy>;
  private eventQueue: Array<IRecorderEvent>;
  private options: BatchEventRecorderOptions;
  private tempEventRepository: Repository<RecorderTempEvent>;
  private dataSource: DataSource;
  private eventTypeRepository: Repository<EventType>;
  private recordingRepository: Repository<Recording>;
  private namespaces: ArtifactNamespace[];
  private types: ArtifactType[];
  private flusher: IFlusher;
  private range: Range | undefined;
  private emitter: EventEmitter;
  private closing: boolean;
  private recorderOptions: EventRecorderOptions;
  private queueSize: number;
  private recordedHistory: Record<string, boolean>;
  private eventTypeIdMap: Record<number, EventType>;
  private recorderEventTypeStringIdMap: Record<string, IRecorderEventType>;
  private eventTypeNameAndVersionMap: Record<string, Record<number, EventType>>;
  private recorderId: string;
  private batchCounter: number;
  private tableCounter: number;
  private initialized: boolean;
  private _preCommitTableName: string;
  private isPreCommitTableOpen: boolean;
  private committing: boolean;

  constructor(
    dataSource: DataSource,
    recordingRepository: Repository<Recording>,
    tempEventRepository: Repository<RecorderTempEvent>,
    eventTypeRepository: Repository<EventType>,
    options?: Partial<BatchEventRecorderOptions>,
  ) {
    this.dataSource = dataSource;
    this.recordingRepository = recordingRepository;
    this.tempEventRepository = tempEventRepository;
    this.eventTypeRepository = eventTypeRepository;
    this.eventTypeStrategies = {};
    this.options = _.merge(defaultBatchEventRecorderOptions, options);
    this.flusher =
      options?.flusher ||
      new TimeoutBatchedFlusher(
        this.options.flushIntervalMs,
        this.options.maxBatchSize,
      );
    this.queueSize = 0;
    this.emitter = new EventEmitter();
    this.closing = false;
    this.recorderOptions = {
      overwriteExistingEvents: false,
    };
    this.recordedHistory = {};
    this.eventTypeIdMap = {};
    this.eventTypeNameAndVersionMap = {};
    this.recorderEventTypeStringIdMap = {};
    this.recorderId = randomUUID();
    this.eventQueue = [];
    this.batchCounter = 0;
    this.tableCounter = 0;
    this.initialized = false;
    this.isPreCommitTableOpen = false;
    this._preCommitTableName = "";
    this.committing = false;

    this.emitter.setMaxListeners(this.options.maxBatchSize * 3);
    // Setup flush event handler
    this.flusher.onFlush(async () => {
      logger.debug(`flushing all queued events`);
      try {
        await this.flushAll();
        logger.debug("flush cycle completed");
        this.emitter.emit("flush");
      } catch (err) {
        logger.error(`error caught flushing ${err}`);
        logger.error(err);
        this.emitter.emit("error", err);
      }
    });
  }

  async begin(): Promise<void> {
    if (!this.initialized) {
      logger.debug("saving recording details for later cleanup");
      await this.recordingRepository.insert({
        recorderId: this.recorderId,
        expiration: DateTime.now().plus({ day: 1 }).toJSDate(),
      });
      this.initialized = true;
    }

    if (this.isPreCommitTableOpen) {
      throw new RecorderError("Only one temporary table may be set at a time");
    }

    // Create a temporary table to collect precommit events
    const formattedRecorderId = this.recorderId.replace(/-/g, "_");
    this._preCommitTableName = `recorder_pre_commit_${formattedRecorderId}_${this.tableCounter}`;
    this.tableCounter += 1;
    this.isPreCommitTableOpen = true;

    await this.dataSource.query(`
      CREATE TABLE ${this.preCommitTableName} AS 
      TABLE "event"
      WITH NO DATA
    `);
    logger.debug(`created temporary table ${this.preCommitTableName}`);
  }

  private get preCommitTableName(): string {
    if (this._preCommitTableName === "") {
      throw new RecorderError("need to call begin before recording");
    }
    return this._preCommitTableName;
  }

  async commit(): Promise<IRecorderCommitResult> {
    logger.debug(`committing changes to ${this.preCommitTableName}`);
    this.committing = true;
    // Flush whatever is in the
    this.flusher.clear();

    try {
      await this.flushAll();
    } catch (err) {
      // No need to stop committing. We will commit what can possibly be
      // committed
      logger.debug(
        "error on flush before commit. errors will appear with events",
      );
    }

    // Using the recorder_temp_event table we can commit all of the events
    // Remove anything with duplicates
    const t1 = timer("delete event dupes");
    let response: IRecorderCommitResult;
    try {
      const [invalid, uncommittedCount] = (await this.dataSource.query(`
      WITH events_with_duplicates AS (
        SELECT 
          pct."sourceId", 
          pct."typeId",
          COUNT(*) as "count"
        FROM ${this.preCommitTableName} AS pct
        GROUP BY 1,2
        HAVING COUNT(*) > 1
      )
      DELETE FROM ${this.preCommitTableName} p
      USING events_with_duplicates ewd
      WHERE p."sourceId" = ewd."sourceId" AND
            p."typeId" = ewd."typeId" AND
            ewd."typeId" IS NOT NULL AND
            ewd."sourceId" IS NOT NULL
      RETURNING p."sourceId", p."typeId"
    `)) as [{ sourceId: string; typeId: number }[], number];
      t1();
      logger.debug(`deleted ${uncommittedCount} events with duplicates`);

      logger.debug("committing to event database");
      // Write back into the main database
      type Result = { sourceId: string; typeId: number };
      const successful = await this.dataSource.transaction(async (manager) => {
        const t2 = timer("commit to event table");
        const response = (await manager.query(`
          WITH write_to_canonical_event AS (
            INSERT INTO event ("sourceId", "typeId", "time", "toId", "fromId", "amount", "details")
            SELECT "sourceId", "typeId", "time", "toId", "fromId", "amount", "details" FROM ${this.preCommitTableName}
            ON CONFLICT ("sourceId", "typeId", "time") DO NOTHING
            RETURNING "sourceId", "typeId"
          )
          SELECT p."sourceId", p."typeId", CASE WHEN w."typeId" IS NOT NULL THEN 0 ELSE 1 END AS "skipped"
          FROM ${this.preCommitTableName} p
          LEFT JOIN write_to_canonical_event w
            ON w."sourceId" = p."sourceId" AND p."typeId" = w."typeId"
        `)) as (Result & { skipped: number })[];
        t2();

        logger.debug("dropping the table");
        const t3 = timer("drop table");
        await manager.query(`
          DROP TABLE ${this.preCommitTableName}
        `);
        t3();
        return response;
      });

      const { committed, skipped } = successful.reduce<{
        committed: Result[];
        skipped: Result[];
      }>(
        (a, c) => {
          if (c.skipped) {
            a.skipped.push(c);
          } else {
            a.committed.push(c);
          }
          return a;
        },
        { committed: [], skipped: [] },
      );

      const uniqueCommittedEvents = new UniqueArray<RecorderEventRef>(
        eventUniqueId,
      );

      const convertResp = (c: { sourceId: string; typeId: number }) => {
        const t = RecorderEventType.fromDBEventType(
          this.eventTypeIdMap[c.typeId],
        );
        return {
          sourceId: c.sourceId,
          type: t,
        };
      };
      const committedEvents = committed.map(convertResp);
      const skippedEvents = skipped.map(convertResp);
      const invalidEvents = invalid.map(convertResp);
      invalidEvents.forEach((e) => {
        uniqueCommittedEvents.push(e);
      });

      if (committedEvents.length > 0) {
        logger.debug(
          `notifying of event completions for ${committedEvents.length} committed events`,
        );
        this.notifySuccess(committedEvents);
      }
      if (skippedEvents.length > 0) {
        logger.debug(
          `notifying of event completions for ${skippedEvents.length} skipped events`,
        );
        this.notifySuccess(skippedEvents);
      }
      if (invalidEvents.length > 0) {
        logger.debug(
          `notifying of event failures for ${invalidEvents.length} invalid events`,
        );
        this.notifyFailure(
          uniqueCommittedEvents.items(),
          new RecorderError(
            "event has duplicates in this collection. something is wrong with the collector",
          ),
        );
      }
      response = {
        committed: committedEvents.map(eventUniqueId),
        skipped: skippedEvents.map(eventUniqueId),
        invalid: uniqueCommittedEvents.items().map(eventUniqueId),
        errors: [],
      };
    } catch (err) {
      this.emitter.emit("commit-error", err);
      response = {
        committed: [],
        invalid: [],
        skipped: [],
        errors: [err],
      };
    }
    this._preCommitTableName = "";
    this.isPreCommitTableOpen = false;
    this.committing = false;
    return response;
  }

  async wait(
    handles: RecordHandle[],
    timeoutMs?: number,
  ): Promise<AsyncResults<RecordResponse>> {
    timeoutMs = timeoutMs === undefined ? this.options.timeoutMs : timeoutMs;

    const results: AsyncResults<RecordResponse> = {
      success: [],
      errors: [],
    };

    const expectedMap: Record<string, number> = {};
    let expectedCount = 0;

    handles.forEach((h) => {
      // We can skip things that have already been recorded
      if (this.isKnownByIdStr(h.id)) {
        return;
      }

      expectedMap[h.id] = 1;
      expectedCount += 1;
    });
    if (expectedCount === 0) {
      return results;
    }

    return new Promise((resolve, reject) => {
      let count = 0;
      const timeout = setTimeout(() => {
        return reject(
          new RecorderError("timed out waiting for recordings to complete"),
        );
      }, timeoutMs);

      const stopListening = () => {
        this.emitter.removeListener("event-record-failure", failure);
        this.emitter.removeListener("event-record-success", success);
        clearTimeout(timeout);
      };

      const eventCallback = (err: unknown | null, uniqueId: string) => {
        if (expectedMap[uniqueId] === 1) {
          expectedMap[uniqueId] = 0;
          count += 1;

          if (err) {
            results.errors.push(err);
          } else {
            results.success.push(uniqueId);
          }

          // Why's it greater tho?
          if (expectedCount >= count) {
            stopListening();
            return resolve(results);
          }
        }
      };

      const failure = (err: unknown, uniqueId: string) => {
        eventCallback(err, uniqueId);
      };
      const success = (uniqueId: string) => {
        eventCallback(null, uniqueId);
      };

      this.emitter.addListener("commit-error", (err: unknown) => {
        stopListening();
        return reject(err);
      });

      this.emitter.addListener("event-record-failure", failure);

      this.emitter.addListener("event-record-success", success);
    });
  }

  private async waitTillAvailable(): Promise<void> {
    if (!this.isQueueFull()) {
      return;
    }
    logger.debug("recorder: waiting till available");
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error("timed out waiting for recorder to become available"));
      }, this.options.timeoutMs);

      const checkQueue = () => {
        // Start event waiting loop for flushes
        if (!this.isQueueFull()) {
          clearTimeout(timeout);
          resolve();
        } else {
          logger.debug("recorder queue full. applying backpressure");
          this.emitter.once("flush", checkQueue);
        }
      };
      checkQueue();
    });
  }

  private isQueueFull() {
    return this.queueSize >= this.options.maxBatchSize;
  }

  setActorScope(namespaces: ArtifactNamespace[], types: ArtifactType[]) {
    this.namespaces = namespaces;
    this.types = types;
  }

  setRange(range: Range) {
    // This is used to optimize queries.
    this.range = range;
  }

  setOptions(options: EventRecorderOptions): void {
    if (options.overwriteExistingEvents) {
      logger.debug("setting recorder to overwrite existing events");
    }
    this.recorderOptions = options;
  }

  async setup() {
    await this.loadEventTypes();
  }

  async loadEventTypes() {
    // Load all event types from the database. This is not expected to change during
    // execution so this should only happen once.
    const eventTypes = await this.eventTypeRepository.find();

    eventTypes.forEach((t) => {
      this.eventTypeIdMap[t.id] = t;
      const recorderEventType = RecorderEventType.fromDBEventType(t);
      this.recorderEventTypeStringIdMap[recorderEventType.toString()] =
        recorderEventType;
      const nameAndVersionMap: Record<number, EventType> =
        this.eventTypeNameAndVersionMap[t.name] || {};

      nameAndVersionMap[t.version] = t;
      this.eventTypeNameAndVersionMap[t.name] = nameAndVersionMap;
    });
  }

  private isKnownByIdStr(id: string) {
    return this.recordedHistory[id] === true;
  }

  // Records events into a queue and periodically flushes that queue as
  // transactions to the database.
  registerEventType(strategy: IEventTypeStrategy): void {
    this.eventTypeStrategies[strategy.type.toString()] = strategy;
  }

  async record(input: IncompleteEvent): Promise<RecordHandle> {
    if (this.committing) {
      throw new RecorderError("recorder is committing. writes disallowed");
    }
    if (this.closing) {
      throw new RecorderError("recorder is closing. writes disallowed");
    }
    const event = RecorderEvent.fromIncompleteEvent(input);

    await this.waitTillAvailable();

    // Queue an event for writing
    this.eventQueue.push(event);
    this.queueSize += 1;

    // Upon the first "record" begin the flush sequence
    this.scheduleFlush(1);

    const uniqueId = eventUniqueId(event);

    return {
      id: uniqueId,
      wait: () => {
        // Let's not unnecessarily make a bunch of event listeners
        if (this.recordedHistory[uniqueId]) {
          return Promise.resolve(uniqueId);
        }

        return new Promise((resolve, reject) => {
          this.emitter.addListener(uniqueId, (err) => {
            if (err) {
              return reject(err);
            }
            return resolve(uniqueId);
          });
        });
      },
    };
  }

  addListener(listener: string, callback: (...args: any) => void) {
    return this.emitter.on(listener, callback);
  }

  removeListener(listener: string, callback: (...args: any) => void) {
    this.emitter.removeListener(listener, callback);
  }

  private scheduleFlush(size: number) {
    this.flusher.notify(size);
  }

  private async flushAll() {
    const batchId = this.batchCounter;
    this.batchCounter += 1;
    const processing = this.eventQueue;
    this.eventQueue = [];
    try {
      await this.processEvents(batchId, processing);
    } catch (err) {
      logger.error(
        `error caught while processing one of the events in batch[${this.recorderId}:${batchId}]`,
        err,
      );

      // Report errors to all of the promises listening on specific events
      this.notifyFailure(processing, err);
      throw err;
    }

    this.queueSize = 0;
  }

  async close(): Promise<void> {
    if (this.closing) {
      throw new RecorderError("there should only be one call to close()");
    }

    // If we have something open we need to commit it and close;

    // Lock the recorder
    this.closing = true;
    return new Promise<void>((resolve, reject) => {
      logger.debug("closing the recorder");

      const timeout = setTimeout(() => {
        reject(new RecorderError("timed out closing the recorder"));
      }, this.options.timeoutMs);

      const closeAll = () => {
        this.emitter.removeAllListeners();
        this.flusher.clear();
        clearTimeout(timeout);
      };
      if (this.isPreCommitTableOpen) {
        this.commit()
          .then(() => {
            logger.debug("recorder flushed and committed");
            closeAll();
            resolve();
          })
          .catch((err) => {
            closeAll();
            reject(err);
          });
      } else {
        closeAll();
        resolve();
      }
    });
  }

  private async processEvents(
    batchId: number,
    processing: IRecorderEvent[],
  ): Promise<void> {
    if (processing.length === 0) {
      logger.debug(`nothing queued for batch[${this.recorderId}:${batchId}]`);
      return;
    }

    const newEvents = [];
    // Filter things that are out of the expected range
    for (const event of processing) {
      // Ignore events outside the range of events if we're not overwriting
      // things otherwise everything is in play
      if (
        !isWithinRange(this.range!, event.time) &&
        !this.recorderOptions.overwriteExistingEvents
      ) {
        logger.debug(`${batchId}: received event out of range. skipping`);
        this.notifySuccess([event]);
        continue;
      }
      newEvents.push(event);
    }

    const dbEvents = this.createEventsFromRecorderEvents(batchId, newEvents);

    // Insert events into the temp event table
    try {
      const result = (await this.retryDbCall(() => {
        return this.tempEventRepository.query(
          `
          INSERT INTO recorder_temp_event
            (
              "recorderId", "batchId", "sourceId", "typeId", "time", 
              "toName", "toNamespace", "toType", "toUrl", 
              "fromName", "fromNamespace", "fromType", "fromUrl", 
              "amount", "details"
            )
            (
              select * from unnest(
                $1::uuid[], $2::int[], $3::text[], $4::int[], $5::timestamptz[],
                $6::text[], $7::artifact_namespace_enum[], $8::artifact_type_enum[], $9::text[],
                $10::text[], $11::artifact_namespace_enum[], $12::artifact_type_enum[], $13::text[],
                $14::float[], $15::jsonb[]
              )
            )
          RETURNING "id"
        `,
          [
            dbEvents.recorderIds,
            dbEvents.batchIds,
            dbEvents.sourceIds,
            dbEvents.typeIds,
            dbEvents.times,
            dbEvents.toNames,
            dbEvents.toNamespaces,
            dbEvents.toTypes,
            dbEvents.toUrls,
            dbEvents.fromNames,
            dbEvents.fromNamespaces,
            dbEvents.fromTypes,
            dbEvents.fromUrls,
            dbEvents.amounts,
            dbEvents.details,
          ],
        );
      })) as { id: number }[];
      if (result.length !== newEvents.length) {
        throw new RecorderError(
          `recorder writes failed. Expected ${newEvents.length} writes but only received ${result.length}`,
        );
      }
      logger.debug(
        `completed writing batch of ${result.length} to the temporary table`,
      );
    } catch (err) {
      logger.error("encountered an error writing to the temporary table");
      logger.debug(typeof err);
      logger.error(`Error type=${typeof err}`);
      logger.error(`Error as JSON=${JSON.stringify(err)}`);
      logger.error(err);
      this.notifyFailure(newEvents, err);
      this.emitter.emit("error", err);
    }

    // Run queries to commit events into the event database
    const eventsWrite = async () => {
      return this.dataSource.transaction(async (manager) => {
        // Write artifacts
        const t0 = timer("write new artifacts");
        const artifactResponse = (await manager.query(
          `
          with new_artifact as (
            SELECT 
              rtea."name" AS "name", 
              rtea."namespace" AS "namespace", 
              rtea."type" AS "type", 
              (array_agg(rtea."url"))[1] AS "url"
            FROM recorder_temp_event_artifact AS rtea
            WHERE 
              rtea."recorderId" = $1 AND
              rtea."batchId" = $2
            GROUP BY 1,2,3
          ), artifact_insert AS (
            INSERT INTO artifact("name", "namespace", "type", "url")
            SELECT * FROM new_artifact
            ON CONFLICT ("name", "namespace") DO NOTHING
            RETURNING "id"
          )
          select count(*) from artifact_insert
      `,
          [this.recorderId, batchId],
        )) as { count: string }[];
        t0();
        if (artifactResponse.length !== 1) {
          throw new RecorderError("unexpected response writing artifacts");
        }
        logger.debug(`added ${artifactResponse[0].count} new artifacts`);

        if (this.recorderOptions.overwriteExistingEvents) {
          // Delete existing events
          const t1 = timer("delete existing events");
          await manager.query(
            `
            DELETE FROM event e
            USING recorder_temp_event rte
            WHERE rte."sourceId" = e."sourceId" AND
                  rte."typeId" = e."typeId" AND
                  rte."recorderId" = $1 AND
                  rte."batchId" = $2
          `,
            [this.recorderId, batchId],
          );
          t1();
        }

        const t2 = timer("bulk write");
        // Write all events and delete anything necessary. Ignore events with
        // duplicates we don't know what to do in that case. Leave those in the
        // database.
        const batchResp = (await manager.query(
          `
          with event_with_artifact AS (
            SELECT
              rte."sourceId",
              rte."typeId",
              rte."time",
              a_to."id" AS "toId",
              a_from."id" AS "fromId",
              rte."amount",
              rte."details",
              rte."recorderId"
            FROM recorder_temp_event AS rte
            LEFT JOIN artifact a_to 
              ON rte."toName" = a_to."name" AND
                 rte."toNamespace" = a_to."namespace"
            LEFT JOIN artifact a_from 
              ON rte."fromName" = a_from."name" AND
                 rte."fromNamespace" = a_from."namespace"
            WHERE 
              rte."recorderId" = $1 AND
              rte."batchId" = $2
          ), batch as (
            INSERT INTO ${this.preCommitTableName} ("sourceId", "typeId", "time", "toId", "fromId", "amount", "details")
            SELECT "sourceId", "typeId", "time", "toId", "fromId", "amount", "details" FROM event_with_artifact
            RETURNING "id"
          )
          select count(*) from batch;
      `,
          [this.recorderId, batchId],
        )) as { count: string }[];
        t2();

        if (batchResp.length !== 1) {
          throw new RecorderError("error occurred counting the batch results");
        }

        // COPY the temp table to the real one
        logger.debug(
          `finished writing ${batchResp[0].count} events to the temporary table`,
        );
        return batchResp;
      });
    };

    try {
      await this.retryDbCall(eventsWrite, 3);
    } catch (err) {
      this.notifyFailure(newEvents, err);
    }

    logger.info(`finished flushing for batch[${this.recorderId}:${batchId}]`);
  }

  protected async retryDbCall<T>(
    cb: () => Promise<T>,
    retryCount: number = 10,
  ): Promise<T> {
    let timeoutMs = 100;
    for (let i = 0; i < retryCount; i++) {
      try {
        return await cb();
      } catch (err) {
        // Throw the final error
        if (i === retryCount - 1) {
          throw err;
        }
        if (err === undefined) {
          logger.debug(
            `received an undefined error from the database. sleeping then retrying`,
          );
          await asyncTimeout(timeoutMs);
          timeoutMs += timeoutMs;
        } else {
          throw err;
        }
      }
    }
    throw new RecorderError(`maximum retries for database call reached.`);
  }

  protected notifySuccess(events: RecorderEventRef[]) {
    events.forEach((e) => {
      // Mark as known event
      const uniqueId = eventUniqueId(e);
      this.recordedHistory[uniqueId] = true;

      // Notify any subscribers that the event has been recorded
      this.emitter.emit(uniqueId, null, uniqueId);
      this.emitter.emit("event-record-success", uniqueId);
    });
  }

  protected notifyFailure(events: RecorderEventRef[], err: unknown) {
    events.forEach((e) => {
      // Notify any subscribers that the event has failed to record
      const uniqueId = eventUniqueId(e);
      this.recordedHistory[uniqueId] = true;

      this.emitter.emit(uniqueId, err, "");
      this.emitter.emit("event-record-failure", err, uniqueId);
      // FIXME... this should be a wrapped error
      this.emitter.emit(
        "error",
        new RecorderError(`error recording ${uniqueId}`),
      );
    });
  }

  protected createEventsFromRecorderEvents(
    batchId: number,
    recorderEvents: IRecorderEvent[],
  ): PGRecorderTempEventBatchInput {
    const inputs: PGRecorderTempEventBatchInput = {
      recorderIds: [],
      batchIds: [],
      sourceIds: [],
      typeIds: [],
      times: [],
      toNames: [],
      toNamespaces: [],
      toTypes: [],
      toUrls: [],
      fromNames: [],
      fromNamespaces: [],
      fromTypes: [],
      fromUrls: [],
      amounts: [],
      details: [],
    };
    recorderEvents.forEach((e) => {
      const eventType = this.resolveEventType(e.type);

      inputs.recorderIds.push(this.recorderId);
      inputs.batchIds.push(batchId);
      inputs.sourceIds.push(e.sourceId);
      inputs.typeIds.push(eventType.id.valueOf());
      inputs.times.push(e.time.toJSDate());
      inputs.toNames.push(e.to.name);
      inputs.toNamespaces.push(e.to.namespace);
      inputs.toTypes.push(e.to.type);
      inputs.toUrls.push(e.to.url || null);
      inputs.fromNames.push(e.from?.name || null);
      inputs.fromNamespaces.push(e.from?.namespace || null);
      inputs.fromTypes.push(e.from?.type || null);
      inputs.fromUrls.push(e.from?.url || null);
      inputs.amounts.push(e.amount);
      inputs.details.push(e.details);
    });
    return inputs;
  }

  protected resolveEventTypeById(typeId: number) {
    return this.eventTypeIdMap[typeId];
  }

  protected resolveEventType(type: IRecorderEventType) {
    const versions = this.eventTypeNameAndVersionMap[type.name] || {};
    const resolved = versions[type.version];
    if (!resolved) {
      throw new RecorderError(
        `Event type ${type.name} v${type.version} does not exist`,
      );
    }
    return resolved;
  }
}
