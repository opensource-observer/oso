import {
  Artifact,
  Event,
  ArtifactNamespace,
  ArtifactType,
} from "../db/orm-entities.js";
import { FindOptionsWhere } from "typeorm";
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
  id: string;
  wait(): Promise<RecordResponse>;
}

export interface CommitResult {
  committed: string[];
  skipped: string[];
  invalid: string[];
  errors: unknown[];
}

export interface IEventRecorderClient {
  // Record a single event. These are batched
  record(event: IncompleteEvent): Promise<RecordHandle>;

  wait(
    handles: RecordHandle[],
    timeoutMs?: number,
  ): Promise<AsyncResults<RecordResponse>>;
}

export interface IEventRecorder extends IEventRecorderClient {
  setup(): Promise<void>;

  setActorScope(namespaces: ArtifactNamespace[], types: ArtifactType[]): void;

  setRange(range: Range): void;

  setOptions(options: EventRecorderOptions): void;

  begin(): Promise<void>;
  commit(): Promise<CommitResult>;
  rollback(): Promise<void>;

  // Call this when you're done recording
  close(): Promise<void>;

  addListener(listener: "error", cb: (err: unknown) => void): EventEmitter;
  addListener(listener: "flush-complete", cb: () => void): EventEmitter;

  removeListener(listener: "error", cb: (err: unknown) => void): void;
  removeListener(listener: "flush-complete", cb: (err: unknown) => void): void;
}

export type RecorderFactory = () => Promise<IEventRecorder>;

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
  type: IRecorderEventType;

  // This is the query to use to get all of the events of a specific EventType
  all(directory: IActorDirectory): FindOptionsWhere<Event>;

  idFromEvent(directory: IActorDirectory, event: Event): Promise<string>;

  idFromIncompleteEvent(
    directory: IActorDirectory,
    event: IRecorderEvent,
  ): Promise<string>;
}

export type IncompleteActor<N, M> = {
  name: N;
  namespace: M;
};

export type IncompleteArtifact = {
  name: string;
  namespace: ArtifactNamespace;
  type: ArtifactType;
} & Partial<Artifact>;

export interface IRecorderEventType {
  name: string;
  version: number;
  toString(): string;
}

export type IncompleteEventType = Pick<IRecorderEventType, "name" | "version">;

export interface IncompleteEvent {
  time: DateTime;
  type: IRecorderEventType;
  sourceId: string;
  to: IncompleteArtifact;
  from?: IncompleteArtifact;
  amount: number;
  details?: object;
  size?: bigint;
}

export interface IRecorderEvent {
  id: number | null;
  time: DateTime;
  type: IRecorderEventType;
  sourceId: string;
  to: IncompleteArtifact;
  from: IncompleteArtifact | null;
  amount: number;
  details: object;
}

export type EventGroupRecorderCallback<T> = (results: AsyncResults<T>) => void;

export interface IEventGroupRecorder<G> {
  record(event: IncompleteEvent): Promise<void>;

  wait(group: G): Promise<AsyncResults<string>>;

  commit(): void;

  addListener(message: "error", cb: (err: unknown) => void): EventEmitter;
  addListener(
    message: "group-completed",
    cb: (id: number) => void,
  ): EventEmitter;

  removeListener(message: "error", cb: (err: unknown) => void): void;
  removeListener(message: "group-completed", cb: (id: number) => void): void;
}
