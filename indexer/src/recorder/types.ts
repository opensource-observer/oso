import {
  Artifact,
  Contributor,
  EventType,
  Event,
  Prisma,
} from "@prisma/client";
import _ from "lodash";
import { DateTime } from "luxon";

export class UnknownActor extends Error {
  constructor(message: string) {
    super(message);

    Object.setPrototypeOf(this, UnknownActor.prototype);
  }
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
  record(event: IncompleteEvent): void;

  setActorScope(
    artifactNamespaces: string[],
    contributorNamespaces: string[],
  ): void;

  // Call this when you're done recording
  waitAll(): Promise<void[]>;

  wait(eventType: EventType): Promise<void>;
}

export interface IActorDirectory {
  artifactFromId(id: number): Promise<Artifact>;
  contributorFromId(id: number): Promise<Contributor>;

  resolveContributorId(contributor: IncompleteContributor): Promise<number>;
  resolveArtifactId(artifact: IncompleteArtifact): Promise<number>;

  knownArtifactsFrom(artifacts: IncompleteArtifact[]): Artifact[];
  knownContributorsFrom(contributors: IncompleteContributor[]): Contributor[];

  unknownArtifactsFrom(artifacts: IncompleteArtifact[]): IncompleteArtifact[];
  unknownContributorsFrom(
    contributors: IncompleteContributor[],
  ): IncompleteContributor[];
}

export interface IEventTypeStrategy {
  // This library assumes that each event type has a way of determining
  // uniqueness with events. This is for idempotency's sake. Most of the time
  // this likely doesn't need to be used.
  //uniqueEventsQueryFor(resolver: IActorResolver, events: IncompleteEvent[]): Prisma.EventWhereInput;

  // This is the query to use to get all of the events of a specific EventType
  all(directory: IActorDirectory): Prisma.EventWhereInput;

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
export type IncompleteContributor = Pick<Contributor, "name" | "namespace"> &
  Partial<Contributor>;

export type IncompleteEvent = {
  eventTime: DateTime;
  eventType: EventType;
  artifact: IncompleteArtifact;
  contributor?: IncompleteContributor;
  amount: number;
  details?: object;
};

export class BasicEventTypeStrategy implements IEventTypeStrategy {
  private allQuery: Prisma.EventWhereInput;
  private eventIdFun: (
    directory: IActorDirectory,
    event: Event,
  ) => Promise<string>;
  private incompleteIdFunc: (
    directory: IActorDirectory,
    event: IncompleteEvent,
  ) => Promise<string>;

  constructor(
    allQuery: Prisma.EventWhereInput,
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

  all(_directory: IActorDirectory): Prisma.EventWhereInput {
    return _.cloneDeep(this.allQuery);
  }
}

export function generateEventTypeStrategy(
  eventType: EventType,
): IEventTypeStrategy {
  return new BasicEventTypeStrategy(
    {
      eventType: eventType,
    },
    async (directory, event) => {
      const artifact = await directory.artifactFromId(event.artifactId);
      const artifactStr = `${artifact.name}::${artifact.namespace}`;

      let contributorStr = "";
      if (event.contributorId) {
        const contributor = await directory.contributorFromId(
          event.contributorId,
        );
        contributorStr = `${contributor.name}::${contributor.namespace}`;
      }
      // by default the "unique id" will just be the time, event type, and artifact id concatenated
      return `${event.eventTime.toISOString()}::${
        event.eventType
      }::${artifactStr}::${contributorStr}`;
    },
    async (_directory, event) => {
      let contributorStr = "";
      if (event.contributor) {
        contributorStr = `${event.contributor.name}::${event.contributor.namespace}`;
      }
      return `${event.eventTime.toUTC().toISO()}::${event.eventType}::${
        event.artifact.name
      }::${event.artifact.namespace}::${contributorStr}`;
    },
  );
}
