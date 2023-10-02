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
} from "./types.js";
import { In, Repository, And, MoreThanOrEqual, LessThanOrEqual } from "typeorm";
import { InmemActorResolver } from "./actors.js";
import { UniqueArray, asyncBatch } from "../utils/array.js";
import { logger } from "../utils/logger.js";
import _ from "lodash";
import { EntityLookup } from "../utils/lookup.js";
import { PromisePubSub } from "../utils/pubsub.js";

export interface BatchEventRecorderOptions {
  maxBatchSize: number;
}

export type RecordResponse = void;

class EventTypeStorage<T> {
  private queue: UniqueArray<IncompleteEvent>;
  private pubsub: PromisePubSub<T, unknown>;

  static setup<X>(): EventTypeStorage<X> {
    const queue = new UniqueArray<IncompleteEvent>((event) => {
      return event.sourceId;
    });
    return new EventTypeStorage(queue);
  }

  private constructor(queue: UniqueArray<IncompleteEvent>) {
    this.queue = queue;
    this.pubsub = new PromisePubSub();
  }

  pushAndWait(event: IncompleteEvent): Promise<T> {
    this.queue.push(event);

    return this.pubsub.sub(event.sourceId);
  }

  pop(): IncompleteEvent | undefined {
    return this.queue.pop();
  }

  popAll(): IncompleteEvent[] {
    const events = [];
    const lengthToPop = this.length;

    for (let i = 0; i < lengthToPop; i++) {
      const event = this.pop();
      if (event) {
        events.push(event);
      }
    }
    return events;
  }

  emitResponse(sourceId: string, err: unknown | null, res: T) {
    return this.pubsub.pub(sourceId, err, res);
  }

  get length(): number {
    return this.queue.length;
  }
}

const defaultBatchEventRecorderOptions: BatchEventRecorderOptions = {
  maxBatchSize: 5000,
};

export interface IFlusher {
  scheduleIfNotSet(cb: () => void): void;
  clear(): void;
  isScheduled(): boolean;
}

export class TimeoutFlusher implements IFlusher {
  private timeout: NodeJS.Timeout | null;
  private timeoutMs: number;

  constructor(timeoutMs: number) {
    this.timeoutMs = timeoutMs;
    this.timeout = null;
  }

  scheduleIfNotSet(cb: () => void): void {
    if (!this.timeout) {
      this.timeout = setTimeout(cb, this.timeoutMs);
    }
  }

  clear(): void {
    if (this.timeout) {
      clearTimeout(this.timeout);
    }
    this.timeout = null;
  }

  isScheduled(): boolean {
    if (this.timeout) {
      return true;
    }
    return false;
  }
}

export class BatchEventRecorder implements IEventRecorder {
  private eventTypeStrategies: Record<string, IEventTypeStrategy>;
  private eventTypeStorage: Record<string, EventTypeStorage<void>>;
  private options: BatchEventRecorderOptions;
  private actorDirectory: InmemActorResolver;
  private eventRepository: Repository<Event>;
  private artifactRepository: Repository<Artifact>;
  private namespaces: ArtifactNamespace[];
  private types: ArtifactType[];
  private actorsLoaded: boolean;
  private flusher: IFlusher;
  private pubsub: PromisePubSub<void, unknown>;

  constructor(
    eventRepository: Repository<Event>,
    artifactRepository: Repository<Artifact>,
    flusher: IFlusher,
    options?: BatchEventRecorderOptions,
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
    this.pubsub = new PromisePubSub();
  }

  setActorScope(namespaces: ArtifactNamespace[], types: ArtifactType[]) {
    this.namespaces = namespaces;
    this.types = types;
  }

  private async loadActors(): Promise<void> {
    if (this.namespaces.length === 0) {
      throw new Error("scope of recording must be set");
    }

    logger.debug("loading all artifacts and contributors");

    // Load all of the artifacts
    const artifacts = await this.artifactRepository.find({
      where: {
        namespace: In(this.namespaces),
        type: In(this.types),
      },
    });

    let count = 0;
    for await (const raw of artifacts) {
      const artifact = raw as Artifact;
      this.actorDirectory.loadArtifact(artifact);
      count += 1;
    }
    logger.debug(`loaded ${count} artifacts`);
    this.actorsLoaded = true;
  }

  // Records events into a queue and periodically flushes that queue as
  // transactions to the database.
  registerEventType(eventType: EventType, strategy: IEventTypeStrategy): void {
    this.eventTypeStrategies[eventType.toString()] = strategy;
  }

  record(event: IncompleteEvent): Promise<RecordResponse> {
    // Queue an event for writing
    const queue = this.getEventTypeStorage(event.type);
    const promise = queue.pushAndWait(event);

    this.flusher.scheduleIfNotSet(async () => {
      try {
        logger.debug(`flushing all queued events`);
        await this.flushAll();
      } catch {
        logger.debug(`errors flushing`);
      }
      logger.debug("flush complete");
      this.flusher.clear();
    });
    return promise;
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
        logger.error(`error processing events ${eventType}`, err);
      }
    }
  }

  async waitAll(): Promise<void> {
    const all: Promise<void>[] = [];
    for (const eventType in this.eventTypeStorage) {
      all.push(this.wait(eventType as EventType));
    }
    await Promise.all(all);
    return;
  }

  async wait(eventType: EventType): Promise<void> {
    const storage = this.getEventTypeStorage(eventType);
    if (storage.length === 0) {
      return;
    }
    return this.pubsub.sub(eventType);
  }

  private async flushType(eventType: EventType) {
    logger.debug("Waiting for all events to be recorded");
    if (!this.actorsLoaded) {
      await this.loadActors();
    }

    logger.debug(`processing ${eventType}`);
    // Wait for a specific event type queue to complete
    const eventTypeStorage = this.getEventTypeStorage(eventType);
    if (eventTypeStorage.length === 0) {
      logger.debug(`queue empty for ${eventType}`);
      return;
    }

    logger.info(
      `emptying queue for ${eventType.toString()} with ${
        eventTypeStorage.length
      } items`,
    );
    const processing = eventTypeStorage.popAll();
    logger.info(`processing: ${processing.length}`);

    try {
      await this.processEvents(eventType, processing);
      this.pubsub.pub(eventType, null);
    } catch (err) {
      logger.debug("caught error!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!");
      this.pubsub.pub(eventType, err);

      // Report errors to all of the promises listening on specific events
      for (const event of processing) {
        eventTypeStorage.emitResponse(event.sourceId, err);
      }
      throw err;
    }
  }

  private async processEvents(
    eventType: EventType,
    processing: IncompleteEvent[],
  ): Promise<void> {
    // Get the date range for the currently queued items
    const eventTypeStorage = this.getEventTypeStorage(eventType);
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

    // Get event type strategy
    const strategy = this.getEventTypeStrategy(eventType);
    const where = strategy.all(this.actorDirectory);
    where.time = And(
      MoreThanOrEqual(startDate.toJSDate()),
      LessThanOrEqual(endDate.toJSDate()),
    );

    // Find existing events (for idempotency)
    const existingEvents = await this.eventRepository.find({
      where: where,
    });
    const existingEventsLookup: EntityLookup<{
      sourceId: string;
      type: EventType;
    }> = new EntityLookup((e) => `${e.type}:${e.sourceId}`);

    logger.debug("Loaded existing events (if any)");
    existingEvents.forEach((e) => {
      existingEventsLookup.push(e as Event);
    });

    const newEvents = [];
    const queuedArtifacts: UniqueArray<IncompleteArtifact> = new UniqueArray(
      (a) => `${a.name}::${a.namespace}`,
    );

    // Filter duplicates
    for (const event of processing) {
      if (!existingEventsLookup.has(event)) {
        queuedArtifacts.push(event.to);
        if (event.from) {
          queuedArtifacts.push(event.from);
        }
        newEvents.push(event);
      } else {
        // Resolve any existing subscriptions for this event's creation
        eventTypeStorage.emitResponse(event.sourceId, null);
      }
    }
    logger.debug(
      `skipping ${processing.length - newEvents.length} existing events`,
    );

    // Create all of the new actors involved
    const newArtifacts = this.actorDirectory.unknownArtifactsFrom(
      queuedArtifacts.items(),
    );

    // Write all the new artifacts
    await asyncBatch(newArtifacts, this.options.maxBatchSize, async (batch) => {
      logger.debug("writing new artifacts");
      //console.log(batch);
      const artifacts = Artifact.create(batch);
      return this.artifactRepository.insert(artifacts);
    });

    // Load all of the actors again. We can improve this later
    await this.loadActors();

    logger.debug(`about to start writing to db in batch ${newEvents.length}`);

    await asyncBatch(
      newEvents,
      this.options.maxBatchSize,
      async (batch, batchLength) => {
        logger.info(`preparing to write a batch of ${batchLength} events`);
        const events = await Promise.all(
          batch.map(async (e) => {
            const artifactId = await this.actorDirectory.resolveArtifactId(
              e.to,
            );
            let contributorRef: { id: number } | null = null;
            if (e.from) {
              contributorRef = {
                id: await this.actorDirectory.resolveArtifactId(e.from),
              };
            }

            const input = this.eventRepository.create({
              time: e.time.toJSDate(),
              to: {
                id: artifactId,
              },
              from: contributorRef,
              type: e.type,
              amount: e.amount,
              sourceId: e.sourceId,
            });
            return input;
          }),
        );

        try {
          await this.eventRepository.insert(events);
          logger.debug(`completed writing batch of ${batchLength}`);
          events.forEach((e) => {
            eventTypeStorage.emitResponse(e.sourceId, null);
          });
        } catch (err) {
          events.forEach((e) => {
            eventTypeStorage.emitResponse(e.sourceId, e);
          });
          throw err;
        }
      },
    );
  }

  protected getEventTypeStorage(eventType: EventType): EventTypeStorage<void> {
    const typeString = eventType.toString();
    let queue = this.eventTypeStorage[typeString];
    if (!queue) {
      this.eventTypeStorage[typeString] = EventTypeStorage.setup<void>();
      queue = this.eventTypeStorage[typeString];
    }
    return queue;
  }
}
