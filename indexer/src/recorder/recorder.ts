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

export interface BatchEventRecorderOptions {
  maxBatchSize: number;
  timeoutMs: number;
  flushIntervalMs: number;
  tempTableExpirationDays: number;
  flusher?: IFlusher;
}

const defaultBatchEventRecorderOptions: BatchEventRecorderOptions = {
  maxBatchSize: 10000,

  // ten minute timeout seems sane for completing any db writes (in a normal
  // case). When backfilling this should be made much bigger.
  timeoutMs: 600000,

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

export class BatchEventRecorder implements IEventRecorder {
  private eventTypeStrategies: Record<string, IEventTypeStrategy>;
  private eventQueue: UniqueArray<IRecorderEvent>;
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
  private initialized: boolean;

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
    this.eventQueue = new UniqueArray<IRecorderEvent>(eventUniqueId);
    this.batchCounter = 0;
    this.initialized = false;

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
            this.emitter.removeListener("event-record-failure", failure);
            this.emitter.removeListener("event-record-success", success);
            clearTimeout(timeout);
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
    if (this.closing) {
      throw new RecorderError("recorder is closing. should be more writes");
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
    if (!this.initialized) {
      logger.debug("saving recording details for later cleanup");
      await this.recordingRepository.insert({
        recorderId: this.recorderId,
        expiration: DateTime.now().plus({ day: 1 }).toJSDate(),
      });
      this.initialized = true;
    }

    const batchId = this.batchCounter;
    this.batchCounter += 1;
    const processing = this.eventQueue.popAll();
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

    // Lock the recorder
    this.closing = true;
    return new Promise<void>((resolve, reject) => {
      logger.debug("closing the recorder");

      const timeout = setTimeout(() => {
        reject(new RecorderError("timed out closing the recorder"));
      }, this.options.timeoutMs);
      this.flushAll()
        .then(() => {
          logger.debug("final recorder flush complete");
          this.emitter.removeAllListeners();
          this.flusher.clear();
          clearTimeout(timeout);
          resolve();
        })
        .catch(reject);
    });
  }

  // private async flushType(eventType: IRecorderEventType) {
  //   const flushId = randomUUID();
  //   logger.debug(
  //     `${flushId}: Waiting for all ${eventType.toString()} events to be recorded`,
  //   );

  //   // Wait for a specific event type queue to complete
  //   const eventTypeStorage = this.getEventTypeStorage(eventType);
  //   if (eventTypeStorage.length === 0) {
  //     logger.debug(`queue empty for ${eventType.toString()}`);
  //     return;
  //   }

  //   logger.info(
  //     `emptying queue for ${eventType.toString()} with ${eventTypeStorage.length
  //     } items`,
  //   );
  //   const processing = eventTypeStorage.popAll();

  //   try {
  //     await this.processEvents(flushId, eventType, processing);
  //     this.pubsub.pub(eventType.toString(), null);
  //   } catch (err) {
  //     logger.error(
  //       "error caught while processing one of the events in a batch",
  //       err,
  //     );
  //     this.pubsub.pub(eventType.toString(), err);

  //     // Report errors to all of the promises listening on specific events
  //     this.notifyFailure(processing, err);
  //     throw err;
  //   }
  // }

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
      // Ignore events outside the range of events
      if (!isWithinRange(this.range!, event.time)) {
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
        if (artifactResponse.length !== 1) {
          throw new RecorderError("unexpected response writing artifacts");
        }
        logger.debug(`added ${artifactResponse[0].count} new artifacts`);

        if (this.recorderOptions.overwriteExistingEvents) {
          // Delete existing events
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
        }

        // Write all events and delete anything necessary. Ignore events with
        // duplicates we don't know what to do in that case. Leave those in the
        // database.
        const bulkWriteResponse = (await manager.query(
          `
          with current_event_source_ids AS (
            SELECT
              rte_dupes."sourceId",
              rte_dupes."typeId",
              1 AS "num"
            FROM recorder_temp_event AS rte_dupes
            WHERE
              rte_dupes."recorderId" = $1
          ), event_source_ids AS (
            SELECT 
              "sourceId",
              "typeId",
              1 AS "num"
            FROM recorder_temp_duplicate_event
            WHERE
              "recorderId" = $1
            UNION ALL
            SELECT * FROM current_event_source_ids
          ), event_with_duplicates AS (
            SELECT
              "sourceId",
              "typeId",
              SUM(esi."num") as "count"
            FROM event_source_ids esi
            GROUP BY 1,2 
            HAVING SUM(esi."num") > 1
          ), event_with_artifact AS (
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
                 rte."toNamespace" = a_to."namespace" AND
                 rte."toType" = a_to."type"
            LEFT JOIN artifact a_from
              ON rte."fromName" = a_from."name" AND
                 rte."fromNamespace" = a_from."namespace" AND
                 rte."fromType" = a_from."type"
            LEFT JOIN event e
              ON rte."sourceId" = e."sourceId" AND
                 rte."typeId" = e."typeId"
            LEFT JOIN event_with_duplicates ewd
              ON rte."sourceId" = ewd."sourceId" AND
                 rte."typeId" = ewd."typeId"
            WHERE 
              rte."recorderId" = $1 AND
              rte."batchId" = $2 AND
              e."id" IS NULL AND
              ewd."sourceId" IS NULL
          ), commit_events AS (
            INSERT INTO event("sourceId", "typeId", "time", "toId", "fromId", "amount", "details")
            SELECT "sourceId", "typeId", "time", "toId", "fromId", "amount", "details" FROM event_with_artifact
            ON CONFLICT ("sourceId", "typeId", "time") DO NOTHING
            RETURNING "sourceId", "typeId"
          ), commit_events_duplicate_tracking AS (
            INSERT INTO recorder_temp_duplicate_event("recorderId", "sourceId", "typeId")
            SELECT COALESCE($1), commit_events."sourceId", commit_events."typeId" FROM commit_events
            RETURNING "sourceId", "typeId"
          )
          DELETE FROM recorder_temp_event rte_del
          USING commit_events_duplicate_tracking ce
          WHERE rte_del."recorderId" = $1 AND
                rte_del."batchId" = $2 AND
                rte_del."sourceId" = ce."sourceId" AND
                rte_del."typeId" = ce."typeId"
          RETURNING rte_del."sourceId", rte_del."typeId"
      `,
          [this.recorderId, batchId],
        )) as [{ sourceId: string; typeId: number }[], number];
        logger.debug(`bulk write wrote ${bulkWriteResponse[1]} events`);
        return bulkWriteResponse;
      });
    };

    try {
      const response = await this.retryDbCall(eventsWrite, 3);
      const writeCount = response[1];
      if (writeCount !== newEvents.length) {
        // For now duplicates are not treated as errors. This likely needs to
        // change in the future depending on _when_ the duplicate is encounter
        logger.debug(
          `some data wasn't written. it's assumed they are duplicates`,
        );
      }
      this.notifySuccess(newEvents);
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

  protected notifySuccess(events: IRecorderEvent[]) {
    events.forEach((e) => {
      // Mark as known event
      const uniqueId = eventUniqueId(e);
      this.recordedHistory[uniqueId] = true;

      // Notify any subscribers that the event has been recorded
      this.emitter.emit(uniqueId, null, uniqueId);
      this.emitter.emit("event-record-success", uniqueId);
    });
  }

  protected notifyFailure(events: IRecorderEvent[], err: unknown) {
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
