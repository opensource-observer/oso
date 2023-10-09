import {
  Artifact,
  EventType,
  Event,
  ArtifactNamespace,
  ArtifactType,
} from "../db/orm-entities.js";
import { FindOptionsWhere } from "typeorm";
import _ from "lodash";
import { DateTime } from "luxon";
import { GenericError } from "../common/errors.js";
import { Range } from "../utils/ranges.js";
import { EventEmitter } from "node:events";
import { AsyncResults } from "../utils/async-results.js";

export class RecorderError extends GenericError {}
export class GrouperError extends GenericError {}

export class UnknownActor extends RecorderError {}

export interface EventRecorderOptions {
  overwriteExistingEvents: boolean;
}

export type RecordResponse = string;

export interface RecordHandle {
  wait(): Promise<RecordResponse>;
}

export interface IEventRecorder {
  // A generic event recorder that will automatically handle batching writes for
  // events and also resolving artifacts and contributors (and automatically
  // create any that we may need). This is so we don't have to manually control
  // many of the batching calls necessary to make this work reliably with the
  // databases, which apparently can be finicky. It also makes it a bit more
  // generic for us to load events.
  registerEventType(eventType: EventType, strategy: IEventTypeStrategy): void;

  // Record a single event. These are batched
  record(event: IncompleteEvent): Promise<RecordHandle>;

  setActorScope(namespaces: ArtifactNamespace[], types: ArtifactType[]): void;

  setRange(range: Range): void;

  setOptions(options: EventRecorderOptions): void;

  // Call this when you're done recording
  close(): Promise<void>;

  wait(eventType: EventType): Promise<void>;

  addListener(listener: "error", cb: (err: unknown) => void): EventEmitter;
  addListener(listener: "flush-complete", cb: () => void): EventEmitter;

  removeListener(listener: "error", cb: (err: unknown) => void): void;
  removeListener(listener: "flush-complete", cb: (err: unknown) => void): void;
}

export interface IActorDirectory {
  fromId(id: number): Promise<Artifact>;

  resolveArtifactId(artifact: IncompleteArtifact): Promise<number>;

  knownArtifactsFrom(artifacts: IncompleteArtifact[]): Artifact[];

  unknownArtifactsFrom(artifacts: IncompleteArtifact[]): IncompleteArtifact[];
}

export interface IEventTypeStrategy {
  // This library assumes that each event type has a way of determining
  // uniqueness with events. This is for idempotency's sake. Most of the time
  // this likely doesn't need to be used.
  //uniqueEventsQueryFor(resolver: IActorResolver, events: IncompleteEvent[]): Prisma.EventWhereInput;

  // This is the query to use to get all of the events of a specific EventType
  all(directory: IActorDirectory): FindOptionsWhere<Event>;

  idFromEvent(directory: IActorDirectory, event: Event): Promise<string>;

  idFromIncompleteEvent(
    directory: IActorDirectory,
    event: IncompleteEvent,
  ): Promise<string>;
}

export type IncompleteActor<N, M> = {
  name: N;
  namespace: M;
};

export type IncompleteArtifact = Pick<Artifact, "name" | "namespace" | "type"> &
  Partial<Artifact>;

export type IncompleteEvent = {
  time: DateTime;
  type: EventType;
  sourceId: string;
  to: IncompleteArtifact;
  from?: IncompleteArtifact;
  amount: number;
  details?: object;
};

export type EventGroupRecorderCallback<T> = (results: AsyncResults<T>) => void;

export interface IEventGroupRecorder<G> {
  record(event: IncompleteEvent): Promise<void>;

  wait(group: G): Promise<AsyncResults<string>>;

  commit(): void;
}

export class BasicEventTypeStrategy implements IEventTypeStrategy {
  private allQuery: FindOptionsWhere<Event>;
  private eventIdFun: (
    directory: IActorDirectory,
    event: Event,
  ) => Promise<string>;
  private incompleteIdFunc: (
    directory: IActorDirectory,
    event: IncompleteEvent,
  ) => Promise<string>;

  constructor(
    allQuery: FindOptionsWhere<Event>,
    eventIdFunc: (directory: IActorDirectory, event: Event) => Promise<string>,
    incompleteIdFunc: (
      directory: IActorDirectory,
      event: IncompleteEvent,
    ) => Promise<string>,
  ) {
    this.allQuery = allQuery;
    this.eventIdFun = eventIdFunc;
    this.incompleteIdFunc = incompleteIdFunc;
  }

  idFromEvent(directory: IActorDirectory, event: Event): Promise<string> {
    return this.eventIdFun(directory, event);
  }

  idFromIncompleteEvent(
    directory: IActorDirectory,
    event: IncompleteEvent,
  ): Promise<string> {
    return this.incompleteIdFunc(directory, event);
  }

  all(_directory: IActorDirectory): FindOptionsWhere<Event> {
    return _.cloneDeep(this.allQuery);
  }
}

export function generateEventTypeStrategy(
  eventType: EventType,
): IEventTypeStrategy {
  return new BasicEventTypeStrategy(
    {
      type: eventType,
    },
    async (directory, event) => {
      return event.sourceId;
    },
    async (_directory, event) => {
      return event.sourceId;
    },
  );
}
