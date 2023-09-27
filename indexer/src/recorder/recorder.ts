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
//import { streamFindAll as allEvents } from "../db/events.js";
//import { streamFindAll as allContributors } from "../db/contributors.js";
//import { streamFindAll as allArtifacts } from "../db/artifacts.js";
import { logger } from "../utils/logger.js";
import _ from "lodash";
import { EntityLookup } from "../utils/lookup.js";

export interface BatchEventRecorderOptions {
  maxBatchSize: number;
}

const defaultBatchEventRecorderOptions: BatchEventRecorderOptions = {
  maxBatchSize: 5000,
};

export class BatchEventRecorder implements IEventRecorder {
  private eventTypeStrategies: Record<string, IEventTypeStrategy>;
  private eventTypeQueues: Record<string, IncompleteEvent[]>;
  private options: BatchEventRecorderOptions;
  private actorDirectory: InmemActorResolver;
  private eventRepository: Repository<Event>;
  private artifactRepository: Repository<Artifact>;
  private namespaces: ArtifactNamespace[];
  private types: ArtifactType[];
  private actorsLoaded: boolean;

  constructor(
    eventRepository: Repository<Event>,
    artifactRepository: Repository<Artifact>,
    options?: BatchEventRecorderOptions,
  ) {
    this.eventRepository = eventRepository;
    this.artifactRepository = artifactRepository;
    this.eventTypeStrategies = {};
    this.eventTypeQueues = {};
    this.actorDirectory = new InmemActorResolver();
    this.options = _.merge(defaultBatchEventRecorderOptions, options);
    this.namespaces = [];
    this.types = [];
    this.actorsLoaded = false;
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
    this.eventTypeStrategies[eventType] = strategy;
  }

  record(event: IncompleteEvent): void {
    // Queue an event for writing
    const queue = this.getEventTypeQueue(event.type);
    queue.push(event);
  }

  private getEventTypeStrategy(eventType: EventType): IEventTypeStrategy {
    const strategy = this.eventTypeStrategies[eventType];
    if (!strategy) {
      return generateEventTypeStrategy(eventType);
    }
    return strategy;
  }

  async waitAll(): Promise<void[]> {
    // Wait for all queues to complete
    const results: void[] = [];
    for (const eventType in this.eventTypeQueues) {
      results.push(
        await this.wait(EventType[eventType as keyof typeof EventType]),
      );
    }
    return results;
  }

  async wait(eventType: EventType): Promise<void> {
    if (!this.actorsLoaded) {
      await this.loadActors();
    }

    // Wait for a specific event type queue to complete
    const queue = this.getEventTypeQueue(eventType);
    if (queue.length === 0) {
      return;
    }
    this.eventTypeQueues[eventType] = [];

    logger.info(
      `emptying queue for ${eventType.toString()} with ${queue.length} items`,
    );

    // Get the date range for the currently queued items
    let startDate = queue[0].time;
    let endDate = queue[0].time;
    queue.forEach((event) => {
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
    for (const event of queue) {
      if (!existingEventsLookup.has(event)) {
        queuedArtifacts.push(event.to);
        if (event.from) {
          queuedArtifacts.push(event.from);
        }
        newEvents.push(event);
      }
    }
    logger.debug(`skipping ${queue.length - newEvents.length} existing events`);

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

    // Load all of the actors again. We can improve this later
    await this.loadActors();

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

        const response = await this.eventRepository.insert(events);
        logger.debug(`completed writing batch of ${batchLength}`);
        return response;
      },
    );
  }

  protected getEventTypeQueue(eventType: EventType): IncompleteEvent[] {
    let queue = this.eventTypeQueues[eventType];
    if (!queue) {
      this.eventTypeQueues[eventType] = [];
      queue = this.eventTypeQueues[eventType];
    }
    return queue;
  }
}
