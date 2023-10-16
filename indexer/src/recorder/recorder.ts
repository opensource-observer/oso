import {
  Artifact,
  ArtifactNamespace,
  ArtifactType,
  Event,
  EventType,
} from "../db/orm-entities.js";
import {
  IEventRecorder,
  IncompleteEvent,
  IEventTypeStrategy,
  generateEventTypeStrategy,
  IncompleteArtifact,
  RecorderError,
  EventRecorderOptions,
  RecordHandle,
} from "./types.js";
import {
  In,
  Repository,
  And,
  MoreThanOrEqual,
  LessThanOrEqual,
  QueryFailedError,
} from "typeorm";
import { InmemActorResolver } from "./actors.js";
import { UniqueArray, asyncBatch } from "../utils/array.js";
import { logger } from "../utils/logger.js";
import _ from "lodash";
import { PromisePubSub } from "../utils/pubsub.js";
import { Range, isWithinRange } from "../utils/ranges.js";
import { EventEmitter } from "node:events";
import { randomUUID } from "node:crypto";
import { DateTime } from "luxon";
import { EventRef, EventRepository } from "../db/events.js";
import { RecordResponse } from "./types.js";
import { AsyncResults } from "../utils/async-results.js";

export interface BatchEventRecorderOptions {
  maxBatchSize: number;
  timeoutMs: number;
}

class EventTypeStorage {
  private queue: UniqueArray<IncompleteEvent>;

  static setup(): EventTypeStorage {
    const queue = new UniqueArray<IncompleteEvent>((event) => {
      return event.sourceId;
    });
    return new EventTypeStorage(queue);
  }

  private constructor(queue: UniqueArray<IncompleteEvent>) {
    this.queue = queue;
  }

  push(event: IncompleteEvent) {
    this.queue.push(event);
  }

  pop(): IncompleteEvent | undefined {
    return this.queue.pop();
  }

  popAll(): IncompleteEvent[] {
    const events = [];

    while (this.length > 0) {
      const event = this.pop();
      if (event) {
        events.push(event);
      }
    }
    return events;
  }

  get length(): number {
    return this.queue.length;
  }
}

const defaultBatchEventRecorderOptions: BatchEventRecorderOptions = {
  maxBatchSize: 2000,

  // ten minute timeout seems sane for completing any db writes (in a normal
  // case). When backfilling this should be made much bigger.
  timeoutMs: 600000,
};

type FlusherCallback = () => Promise<void>;

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

type KnownEventStorage = {
  loaded: boolean;
  ref: Record<string, EventRef>;
  incompleteRef: Record<string, Omit<EventRef, "id">>;
};

function eventUniqueId(event: Pick<Event, "sourceId" | "type">): string {
  return `${event.type}:${event.sourceId}`;
}

export class BatchEventRecorder implements IEventRecorder {
  private eventTypeStrategies: Record<string, IEventTypeStrategy>;
  private eventTypeStorage: Record<string, EventTypeStorage>;
  private knownEventsStorage: Record<string, KnownEventStorage>;
  private options: BatchEventRecorderOptions;
  private actorDirectory: InmemActorResolver;
  private eventRepository: typeof EventRepository;
  private artifactRepository: Repository<Artifact>;
  private namespaces: ArtifactNamespace[];
  private types: ArtifactType[];
  private actorsLoaded: boolean;
  private flusher: IFlusher;
  private pubsub: PromisePubSub<void, unknown>;
  private range: Range | undefined;
  private emitter: EventEmitter;
  private closing: boolean;
  private recorderOptions: EventRecorderOptions;
  private queueSize: number;
  private lastActorUpdatedAt: DateTime;
  private recordedHistory: Record<string, boolean>;

  constructor(
    eventRepository: typeof EventRepository,
    artifactRepository: Repository<Artifact>,
    flusher: IFlusher,
    options?: Partial<BatchEventRecorderOptions>,
  ) {
    this.eventRepository = eventRepository;
    this.artifactRepository = artifactRepository;
    this.eventTypeStrategies = {};
    this.eventTypeStorage = {};
    this.actorDirectory = new InmemActorResolver();
    this.options = _.merge(defaultBatchEventRecorderOptions, options);
    this.namespaces = [];
    this.types = [];
    this.actorsLoaded = false;
    this.flusher = flusher;
    this.queueSize = 0;
    this.pubsub = new PromisePubSub({
      timeoutMs: this.options.timeoutMs,
    });
    this.knownEventsStorage = {};
    this.emitter = new EventEmitter();
    this.closing = false;
    this.recorderOptions = {
      overwriteExistingEvents: false,
    };
    this.recordedHistory = {};

    // Do you remember...
    this.lastActorUpdatedAt = DateTime.fromISO("1970-09-21T20:00:00Z");
    // Arbitrarily set to an early time

    //this.emitter.setMaxListeners(0);
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
    console.log(`waiting for ${expectedCount}`);

    return new Promise((resolve, reject) => {
      let count = 0;
      setTimeout(() => {
        return reject(
          new RecorderError("timed out waiting for recordings to complete"),
        );
      }, timeoutMs);

      const eventCallback = (err: unknown | null, uniqueId: string) => {
        if (expectedMap[uniqueId] === 1) {
          console.log(uniqueId);
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
    console.log("waiting till available");
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

    // Invalidate any known event storage
    this.knownEventsStorage = {};
  }

  setOptions(options: EventRecorderOptions): void {
    if (options.overwriteExistingEvents) {
      logger.debug("setting recorder to overwrite existing events");
    }
    this.recorderOptions = options;
  }

  private async loadEvents(eventType: EventType) {
    if (!this.range) {
      throw new Error("recorder needs a range to load events");
    }

    if (!this.knownEventsStorageForType(eventType).loaded) {
      logger.debug(`Loading existing events for ${eventType} (if any)`);
      // find all of the events that need for a given time range
      const strategy = this.getEventTypeStrategy(eventType);
      const where = strategy.all(this.actorDirectory);

      where.time = And(
        MoreThanOrEqual(this.range.startDate.toJSDate()),
        LessThanOrEqual(this.range.endDate.toJSDate()),
      );

      // Find existing events (for idempotency)
      const existingEvents = (await this.eventRepository.find({
        where: where,
        select: {
          type: true,
          sourceId: true,
        },
      })) as EventRef[];

      const lookup = existingEvents.reduce<Record<string, EventRef>>(
        (lookup, curr) => {
          lookup[curr.sourceId] = curr;
          return lookup;
        },
        {},
      );

      logger.debug(`existing events length ${existingEvents.length}`);

      this.knownEventsStorage[eventType] = {
        loaded: true,
        ref: lookup,
        incompleteRef: {},
      };
    }
  }

  private knownEventsStorageForType(eventType: EventType): KnownEventStorage {
    const storage = this.knownEventsStorage[eventType] || {
      loaded: false,
      known: {},
    };
    return storage;
  }

  private markEventAsKnown(event: Event | IncompleteEvent) {
    const storage = this.knownEventsStorageForType(event.type);
    if (!storage.loaded) {
      throw new Error(
        `eventType ${event.type} hasn't been loaded for the recorder`,
      );
    }

    // Janky for now
    const uniqueId = eventUniqueId(event);
    this.recordedHistory[uniqueId] = true;

    if ((event as Event).id) {
      storage.ref[event.sourceId] = event as Event;
    } else {
      storage.incompleteRef[event.sourceId] = event;
    }
  }

  private isKnownEvent(event: IncompleteEvent) {
    const storage = this.knownEventsStorageForType(event.type);
    return (
      storage.ref[event.sourceId] !== undefined ||
      storage.incompleteRef[event.sourceId]
    );
  }

  private isKnownByIdStr(id: string) {
    return this.recordedHistory[id] === true;
  }

  private async loadActors(flushId: string): Promise<void> {
    if (this.namespaces.length === 0) {
      throw new Error("scope of recording must be set");
    }

    logger.debug(`${flushId}: loading latest artifacts and contributors`);

    // Load all of the artifacts
    const artifacts = await this.artifactRepository.find({
      where: {
        namespace: In(this.namespaces),
        type: In(this.types),
        updatedAt: MoreThanOrEqual(
          this.lastActorUpdatedAt.startOf("day").toJSDate(),
        ),
      },
      order: {
        updatedAt: "DESC",
      },
    });

    logger.debug(`${flushId}: loaded ${artifacts.length} artifacts`);

    if (artifacts.length > 0) {
      const latestActor = artifacts[0];
      this.lastActorUpdatedAt = DateTime.fromJSDate(latestActor.updatedAt);
    }

    let count = 0;
    for await (const raw of artifacts) {
      const artifact = raw as Artifact;
      this.actorDirectory.loadArtifact(artifact);
      count += 1;
    }
    logger.debug(`${flushId}: loaded ${count} artifacts`);
    this.actorsLoaded = true;
  }

  // Records events into a queue and periodically flushes that queue as
  // transactions to the database.
  registerEventType(eventType: EventType, strategy: IEventTypeStrategy): void {
    this.eventTypeStrategies[eventType.toString()] = strategy;
  }

  async record(event: IncompleteEvent): Promise<RecordHandle> {
    if (this.closing) {
      throw new RecorderError("recorder is closing. should be more writes");
    }

    await this.waitTillAvailable();

    // Queue an event for writing
    const queue = this.getEventTypeStorage(event.type);
    queue.push(event);
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

  private getEventTypeStrategy(eventType: EventType): IEventTypeStrategy {
    const typeString = eventType.toString();
    const strategy = this.eventTypeStrategies[typeString];

    if (!strategy) {
      return generateEventTypeStrategy(eventType);
    }
    return strategy;
  }

  private async flushAll() {
    // Wait for all queues to complete in series
    for (const eventType in this.eventTypeStorage) {
      try {
        await this.flushType(eventType as EventType);
      } catch (err) {
        this.emitter.emit("error", err);
      }
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

      setTimeout(() => {
        reject(new RecorderError("timeout closing the recorder"));
      }, this.options.timeoutMs);
      const all: Promise<void>[] = [];

      for (const eventType in this.eventTypeStorage) {
        all.push(this.waitForEventType(eventType as EventType));
      }

      Promise.all(all)
        .then(() => {
          this.emitter.removeAllListeners();
          this.flusher.clear();
          resolve();
        })
        .catch(reject);
    });
  }

  private async waitForEventType(eventType: EventType): Promise<void> {
    const storage = this.getEventTypeStorage(eventType);
    if (storage.length === 0) {
      return;
    }
    return this.pubsub.sub(eventType);
  }

  private async flushType(eventType: EventType) {
    const flushId = randomUUID();
    logger.debug(
      `${flushId}: Waiting for all ${eventType.toString()} events to be recorded`,
    );
    if (!this.actorsLoaded) {
      await this.loadActors(flushId);
    }

    // Wait for a specific event type queue to complete
    const eventTypeStorage = this.getEventTypeStorage(eventType);
    if (eventTypeStorage.length === 0) {
      logger.debug(`queue empty for ${eventType}`);
      return;
    }

    logger.info(
      `emptying queue for ${eventType.toString()} with ${eventTypeStorage.length
      } items`,
    );
    const processing = eventTypeStorage.popAll();

    try {
      await this.processEvents(flushId, eventType, processing);
      this.pubsub.pub(eventType, null);
    } catch (err) {
      logger.error(
        "error caught while processing one of the events in a batch",
        err,
      );
      this.pubsub.pub(eventType, err);

      // Report errors to all of the promises listening on specific events
      this.notifyFailure(processing, err);
      throw err;
    }
  }

  private async processEvents(
    flushId: string,
    eventType: EventType,
    processing: IncompleteEvent[],
  ): Promise<void> {
    await this.loadEvents(eventType);

    // Get the date range for the currently queued items
    let startDate = processing[0].time;
    let endDate = processing[0].time;
    processing.forEach((event) => {
      if (startDate > event.time) {
        startDate = event.time;
      }

      if (endDate < event.time) {
        endDate = event.time;
      }
    });

    const newEvents = [];
    const updateEvents = [];
    const queuedArtifacts: UniqueArray<IncompleteArtifact> = new UniqueArray(
      (a) => `${a.name}::${a.namespace}`,
    );

    let duplicateAction = "skipping";
    // Filter duplicates
    for (const event of processing) {
      // For now we ignore events outside the range we're recording and any known events.
      if (!this.isKnownEvent(event) && isWithinRange(this.range!, event.time)) {
        queuedArtifacts.push(event.to);
        if (event.from) {
          queuedArtifacts.push(event.from);
        }
        newEvents.push(event);
      } else {
        if (this.recorderOptions.overwriteExistingEvents) {
          duplicateAction = "updating";
          if (event.from) {
            queuedArtifacts.push(event.from);
          }
          updateEvents.push(event);
        } else {
          // Resolve any existing subscriptions for this event's creation
          this.notifySuccess([event]);
        }
      }
    }

    logger.debug(
      `${duplicateAction} ${processing.length - newEvents.length
      } existing events`,
    );

    // Create all of the new actors involved
    const newArtifacts = this.actorDirectory.unknownArtifactsFrom(
      queuedArtifacts.items(),
    );

    // Write all the new artifacts
    await asyncBatch(newArtifacts, this.options.maxBatchSize, async (batch) => {
      logger.debug("writing new artifacts");
      const artifacts = Artifact.create(batch);
      return this.artifactRepository.insert(artifacts);
    });

    if (newArtifacts.length > 0) {
      await this.loadActors(flushId);
    }

    logger.debug(`about to start writing to db in batch ${newEvents.length}`);
    if (newEvents.length === 32) {
      console.log(newEvents);
    }

    // Insert new events
    await asyncBatch(
      newEvents,
      this.options.maxBatchSize,
      async (batch, batchLength) => {
        logger.info(`preparing to write a batch of ${batchLength} events`);
        const events = await this.createEventsFromIncomplete(batch);

        try {
          console.log('boop');
          const result = await this.eventRepository.insert(events);
          console.log('beep222');
          if (result.identifiers.length !== batchLength) {
            throw new RecorderError(
              `recorder writes failed. Expected ${batchLength} writes but only received ${result.identifiers.length}`,
            );
          }
          console.log('beep');
          this.notifySuccess(events);
          logger.debug(
            `completed writing batch of ${result.identifiers.length}`,
          );
        } catch (err) {
          logger.error("encountered an error writing to the database");
          logger.error(err);
          if (err instanceof QueryFailedError) {
            if (err.message.indexOf("duplicate") !== -1) {
              logger.debug("attempted to insert a duplicate event. skipping");
            }
          }
          this.notifyFailure(events, err);
          this.emitter.emit("error", err);
        }
      },
    );

    // Update any events
    await asyncBatch(
      updateEvents,
      this.options.maxBatchSize,
      async (batch, batchLength) => {
        logger.info(`preparing to update a batch of ${batchLength} events`);
        const events = await this.createEventsFromIncomplete(batch);

        try {
          await this.eventRepository.bulkUpdateBySourceIDAndType(events);
          this.notifySuccess(events);
        } catch (err) {
          logger.error("encountered an error updating to the database");
          logger.error(err);
          if (err instanceof QueryFailedError) {
            if (err.message.indexOf("duplicate") !== -1) {
              logger.error(
                "attempted to update but have duplicated event. skipping",
              );
            }
          }
          this.notifyFailure(events, err);
          this.emitter.emit("error", err);
        }
      },
    );
    logger.info(`finished flushing for ${eventType}`);
  }

  protected notifySuccess(events: (Event | IncompleteEvent)[]) {
    events.forEach((e) => {
      // Mark as known event
      this.markEventAsKnown(e);

      const uniqueId = eventUniqueId(e);

      // Notify any subscribers that the event has been recorded
      this.emitter.emit(uniqueId, null, uniqueId);
      this.emitter.emit("event-record-success", uniqueId);
    });
  }

  protected notifyFailure(
    events: Pick<Event, "sourceId" | "type">[],
    err: unknown,
  ) {
    events.forEach((e) => {
      // Notify any subscribers that the event has failed to record
      const uniqueId = eventUniqueId(e);
      this.emitter.emit(uniqueId, err, "");
      this.emitter.emit("event-record-failure", err, uniqueId);
    });
  }

  protected async createEventsFromIncomplete(
    incompleteEvents: IncompleteEvent[],
  ): Promise<Event[]> {
    return await Promise.all(
      incompleteEvents.map(async (e) => {
        const artifactId = await this.actorDirectory.resolveArtifactId(e.to);
        let contributorRef: { id: number } | null = null;
        if (e.from) {
          contributorRef = {
            id: await this.actorDirectory.resolveArtifactId(e.from),
          };
        }
        // Convert size to string
        const size = !e.size ? "0" : e.size.toString(10);

        const input = this.eventRepository.create({
          time: e.time.toJSDate(),
          to: {
            id: artifactId,
          },
          from: contributorRef,
          type: e.type,
          amount: e.amount,
          sourceId: e.sourceId,
          size: size,
          details: e.details,
        });
        return input;
      }),
    );
  }

  protected getEventTypeStorage(eventType: EventType): EventTypeStorage {
    const typeString = eventType.toString();
    let queue = this.eventTypeStorage[typeString];
    if (!queue) {
      this.eventTypeStorage[typeString] = EventTypeStorage.setup();
      queue = this.eventTypeStorage[typeString];
    }
    return queue;
  }
}
