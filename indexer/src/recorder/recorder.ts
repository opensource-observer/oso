import {
  Artifact,
  ArtifactNamespace,
  ArtifactType,
  EventType,
  EventWeakRef,
  Recording,
} from "../db/orm-entities.js";
import {
  IEventRecorder,
  IncompleteEvent,
  IncompleteArtifact,
  RecorderError,
  EventRecorderOptions,
  RecordHandle,
  IRecorderEvent,
  IRecorderEventType,
  ICommitResult as IRecorderCommitResult,
  ICommitResult,
} from "./types.js";
import { Repository } from "typeorm";
import { UniqueArray, asyncBatchFlattened } from "../utils/array.js";
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
import { createClient } from "redis";
import { LRUCache } from "lru-cache";
import { CommitResult } from "./commit-result.js";

type RedisClient = ReturnType<typeof createClient>;

export interface BatchEventRecorderOptions {
  maxBatchSize: number;
  timeoutMs: number;
  flushIntervalMs: number;
  tempTableExpirationDays: number;
  flusher?: IFlusher;
  redisArtifactMetaKey: string;
}

const defaultBatchEventRecorderOptions: BatchEventRecorderOptions = {
  maxBatchSize: 100000,

  // 30 minute timeout as our db seems to be having trouble keeping up
  timeoutMs: 1800000,

  flushIntervalMs: 2000,

  tempTableExpirationDays: 1,

  redisArtifactMetaKey: "artifact::_meta",
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
  event: Pick<IRecorderEvent, "sourceId" | "type" | "to">,
): string {
  return `${event.type}:${event.sourceId}:${event.to.name}:${event.to.namespace}`;
}

function dbEventUniqueId(event: EventWeakRef): string {
  return `${event.typeId}:::${event.toId}:::${event.sourceId}`;
}

function splitDbEventUniqueId(id: string): EventWeakRef {
  const split = _.split(id, ":::");
  return {
    sourceId: split[2],
    typeId: parseInt(split[0]),
    toId: parseInt(split[1]),
  };
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

type ArtifactMatch = [IncompleteArtifact, number | null];
type ArtifactMatches = ArtifactMatch[];
interface IArtifactMap {
  resolveToIds(
    artifacts: (IncompleteArtifact | null)[],
  ): Promise<(number | null)[]>;
  resolveToIncompleteArtifacts(
    ids: (number | null)[],
  ): Promise<(IncompleteArtifact | null)[]>;

  getId(artifact: IncompleteArtifact): Promise<number>;
  getIncomplete(id: number): Promise<IncompleteArtifact>;

  add(pairs: { id: number; artifact: IncompleteArtifact }[]): void;
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
  sourceIds: string[];
  typeIds: number[];
  times: Date[];
  toIds: number[];
  fromIds: OrNull<number>[];
  amounts: number[];
  details: Record<string, any>[];
  uniqueIds: string[];
}

export type RecorderEventRef = Pick<IRecorderEvent, "sourceId" | "type" | "to">;

type ArtifactMetaRedis = {
  lastUpdatedAt: string;
};

export interface ArtifactResolverOptions {
  metaKey: string;
  prefix: string;
  separator: string;
  maxBatchSize: number;
  localLruSize: number;
}

const defaultArtifactResolverOptions: ArtifactResolverOptions = {
  metaKey: "_meta",
  prefix: "artifact",
  separator: ":::",
  maxBatchSize: 100000,
  localLruSize: 300000,
};

type ArtifactLRUStorage = [string, ArtifactNamespace, ArtifactType];

class LRUArtifactMap implements IArtifactMap {
  private toIds: LRUCache<string, number>;
  private toIncomplete: LRUCache<number, ArtifactLRUStorage>;
  private resolver: ArtifactResolver;

  constructor(resolver: ArtifactResolver, size: number) {
    this.toIds = new LRUCache({
      max: size,
    });
    this.toIncomplete = new LRUCache({
      max: size,
    });
    this.resolver = resolver;
  }

  async resolveToIds(
    artifacts: (IncompleteArtifact | null)[],
  ): Promise<(number | null)[]> {
    const unknownArtifacts = artifacts.filter((a) => {
      if (!a) {
        return false;
      }
      const r = this.toIds.get(this.incompleteKey(a));
      return !r;
    }) as IncompleteArtifact[];
    if (unknownArtifacts.length > 0) {
      await this.resolver.idsFromIncompleteArtifacts(unknownArtifacts);
    }
    return artifacts.map((a) => {
      if (!a) {
        return null;
      }
      const id = this.toIds.get(this.incompleteKey(a));
      if (!id) {
        return null;
      }
      return id;
    });
  }

  async resolveToIncompleteArtifacts(
    ids: (number | null)[],
  ): Promise<(IncompleteArtifact | null)[]> {
    const unknownIds = ids.filter((id) => {
      if (!id) {
        return false;
      }
      const r = this.toIncomplete.get(id);
      return !r;
    }) as number[];
    if (unknownIds.length > 0) {
      await this.resolver.incompleteArtifactsByIds(unknownIds);
    }
    return unknownIds.map((id) => {
      if (!id) {
        return null;
      }
      const r = this.toIncomplete.get(id);
      if (!r) {
        return null;
      }
      return this.storageToIncompleteArtifact(r);
    });
  }

  async getId(artifact: IncompleteArtifact): Promise<number> {
    let id: number | null | undefined = this.toIds.get(
      this.incompleteKey(artifact),
    );
    if (!id) {
      id = await this.resolver.idFromIncompleteArtifact(artifact);
      if (!id) {
        throw new Error(
          `artifact is not currently known by incomplete reference "${this.incompleteKey(
            artifact,
          )}"`,
        );
      }
    }
    return id;
  }

  async getIncomplete(id: number): Promise<IncompleteArtifact> {
    const incomplete = this.toIncomplete.get(id);
    if (!incomplete) {
      const resolverIncomplete = await this.resolver.incompleteArtifactById(id);
      if (!resolverIncomplete) {
        throw new Error(`artifact is not currently known by id ${id}`);
      }
      return resolverIncomplete;
    }
    return this.storageToIncompleteArtifact(incomplete);
  }

  add(pairs: { id: number; artifact: IncompleteArtifact }[]): void {
    pairs.forEach(({ id, artifact }) => {
      this.toIds.set(this.incompleteKey(artifact), id);
      this.toIncomplete.set(id, this.incompleteArtifactToStorage(artifact));
    });
  }

  private incompleteArtifactToStorage(
    a: IncompleteArtifact,
  ): ArtifactLRUStorage {
    return [a.name, a.namespace, a.type];
  }

  private storageToIncompleteArtifact(
    s: ArtifactLRUStorage,
  ): IncompleteArtifact {
    return {
      name: s[0],
      namespace: s[1],
      type: s[2],
    };
  }

  private incompleteKey(artifact: IncompleteArtifact) {
    return `${artifact.name}:${artifact.namespace}:${artifact.type}`;
  }
}

/**
 * Mostly an internal class used to resolve artifacts for recording events. This is
 * intended to speed up writes.
 */
export class ArtifactResolver {
  private redis: RedisClient;
  private dataSource: DataSource;
  private options: ArtifactResolverOptions;
  private localMap: LRUArtifactMap;

  constructor(
    dataSource: DataSource,
    redis: RedisClient,
    options?: Partial<ArtifactResolverOptions>,
  ) {
    this.dataSource = dataSource;
    this.redis = redis;
    this.options = _.merge(defaultArtifactResolverOptions, options);
    this.localMap = new LRUArtifactMap(this, this.options.localLruSize);
  }

  async *fullLoadArtifactPages() {
    // during a full load we need to load based on id and calculate the last updated at
    let cursor: number | undefined = 1;
    let lastUpdatedAt = DateTime.fromISO("1970-09-21T00:00:00Z");
    const repo = this.dataSource.getRepository(Artifact);

    logger.debug("load all the artifacts into redis");
    logger.debug("no artifact cache found. running a full load of artifacts");
    do {
      const query = repo
        .createQueryBuilder("artifact")
        .where('artifact."id" > :id', { id: cursor });

      const page = await query
        .orderBy("artifact.id", "ASC")
        .limit(this.options.maxBatchSize)
        .getMany();

      for (const artifact of page) {
        const currentUpdatedAt = DateTime.fromJSDate(artifact.updatedAt);
        if (currentUpdatedAt > lastUpdatedAt) {
          lastUpdatedAt = currentUpdatedAt;
        }
        yield artifact;
      }

      if (page.length < this.options.maxBatchSize) {
        cursor = undefined;
      } else {
        // Ensure that we have everything by including this item
        cursor = page.slice(-1)[0].id;
        logger.debug(`next artifact page starting from ${cursor}`);
      }
    } while (cursor !== undefined);
  }

  async *latestArtifacts(lastUpdatedAt: DateTime) {
    logger.debug("load latest artifacts by updatedAt");
    const formatString = "yyyy-LL-dd HH:mm:ss";

    //let lastUpdatedAt = DateTime.fromISO("1970-09-21T00:00:00Z");
    const repo = this.dataSource.getRepository(Artifact);
    let offset = 0;

    logger.debug(
      `loading artifacts since ${lastUpdatedAt.toFormat(
        formatString,
      )} (${lastUpdatedAt.toISO()})`,
    );
    let cursor: DateTime | undefined = lastUpdatedAt;
    while (cursor !== undefined) {
      const query = repo
        .createQueryBuilder("artifact")
        .where('artifact."updatedAt" > :updatedAt', {
          updatedAt: cursor.toFormat(formatString),
        });

      const page = await query
        .orderBy("artifact.updatedAt", "ASC")
        .limit(this.options.maxBatchSize)
        .offset(offset)
        .getMany();

      offset = this.options.maxBatchSize;
      for (const artifact of page) {
        const currentUpdatedAt = DateTime.fromJSDate(artifact.updatedAt);
        if (currentUpdatedAt.toMillis() != lastUpdatedAt.toMillis()) {
          lastUpdatedAt = currentUpdatedAt;
          offset = 0;
        }
        yield artifact;
      }

      if (page.length < this.options.maxBatchSize) {
        cursor = undefined;
      } else {
        // Ensure that we have everything by including this item
        cursor = DateTime.fromJSDate(page.slice(-1)[0].updatedAt).minus({
          second: 1,
        });
        logger.debug(`next artifact page starting from ${cursor.toISO()}`);
      }
    }
  }

  async loadArtifacts() {
    const formatString = "yyyy-LL-dd HH:mm:ss";
    const artifactMetaJson = await this.redis.get(this.metaKey);
    const artifactMeta: ArtifactMetaRedis =
      artifactMetaJson === null
        ? {
            lastUpdatedAt: DateTime.fromISO("1970-09-21T00:00:00Z")
              .toUTC()
              .toISO(),
          }
        : JSON.parse(artifactMetaJson);

    let lastUpdatedAt = DateTime.fromISO(artifactMeta.lastUpdatedAt);
    const artifactsGenerator = !artifactMetaJson
      ? this.fullLoadArtifactPages()
      : this.latestArtifacts(lastUpdatedAt);

    const loadArtifactsTimer = timer(
      `load artifacts since ${lastUpdatedAt.toFormat(
        formatString,
      )} (${lastUpdatedAt.toISO()})`,
    );
    let count = 0;
    for await (const artifact of artifactsGenerator) {
      count += 1;
      const currentUpdatedAt = DateTime.fromJSDate(artifact.updatedAt);
      if (currentUpdatedAt > lastUpdatedAt) {
        lastUpdatedAt = currentUpdatedAt;
      }
      await this.saveArtifact(artifact);
    }
    loadArtifactsTimer();

    // If the lastUpdatedAt time is earlier than 1 min ago. Set the
    // lastUpdatedAt to 1 min ago. This will eventually speed up look ups
    const oneMinAgo = DateTime.now().toUTC().minus({ minute: 1 });
    if (lastUpdatedAt < oneMinAgo) {
      lastUpdatedAt = oneMinAgo;
    }

    // Set the metadata so we only ever get diffs
    artifactMeta.lastUpdatedAt = lastUpdatedAt.startOf("second").toISO()!;

    await this.redis.set(this.metaKey, JSON.stringify(artifactMeta));
    logger.debug(
      `loaded ${count} artifacts into redis after ${artifactMeta.lastUpdatedAt}`,
    );
  }

  async saveArtifact(artifact: Artifact) {
    const byIncompleteArtifact = this.redis.set(
      this.getKeyByIncompleteArtifact(artifact),
      artifact.id,
    );
    const byId = this.redis.set(
      this.getKeyById(artifact.id),
      JSON.stringify([artifact.name, artifact.namespace, artifact.type]),
    );
    this.addArtifactToLocalMap(artifact);
    return Promise.all([byId, byIncompleteArtifact]);
  }

  addArtifactToLocalMap(artifact: Artifact) {
    this.localMap.add([
      {
        id: artifact.id,
        artifact: {
          name: artifact.name,
          namespace: artifact.namespace,
          type: artifact.type,
        },
      },
    ]);
  }

  addIncompleteArtifactToLocalMap(id: number, artifact: IncompleteArtifact) {
    this.localMap.add([
      {
        id: id,
        artifact: {
          name: artifact.name,
          namespace: artifact.namespace,
          type: artifact.type,
        },
      },
    ]);
  }

  async idFromIncompleteArtifact(
    artifact: IncompleteArtifact,
  ): Promise<number | null> {
    const res = await this.redis.get(this.getKeyByIncompleteArtifact(artifact));
    if (!res) {
      return null;
    }
    const id = parseInt(res);
    this.addIncompleteArtifactToLocalMap(id, artifact);
    return id;
  }

  async idsFromIncompleteArtifacts(artifacts: IncompleteArtifact[]) {
    const res = await this.redis.mGet(
      artifacts.map((a) => this.getKeyByIncompleteArtifact(a)),
    );
    return res.map((r, i) => {
      if (!r) {
        return null;
      }
      const id = parseInt(r);
      this.addIncompleteArtifactToLocalMap(id, artifacts[i]);
      return id;
    });
  }

  private parseIncompleteArtifact(
    result: string | null,
  ): IncompleteArtifact | null {
    if (!result) {
      return null;
    }
    const parsed = JSON.parse(result) as [
      string,
      ArtifactNamespace,
      ArtifactType,
    ];
    return {
      name: parsed[0],
      namespace: parsed[1],
      type: parsed[2],
    };
  }

  async incompleteArtifactById(id: number): Promise<IncompleteArtifact | null> {
    const result = await this.redis.get(this.getKeyById(id));
    const artifact = this.parseIncompleteArtifact(result);
    if (artifact) {
      this.addIncompleteArtifactToLocalMap(id, artifact);
    }
    return artifact;
  }

  async incompleteArtifactsByIds(
    ids: number[],
  ): Promise<Array<IncompleteArtifact | null>> {
    const results = await this.redis.mGet(ids.map((i) => this.getKeyById(i)));
    return results.map((r, i) => {
      const artifact = this.parseIncompleteArtifact(r);
      if (artifact) {
        this.addIncompleteArtifactToLocalMap(ids[i], artifact);
      }
      return artifact;
    });
  }

  private getKey(...parts: string[]) {
    const allParts = [this.options.prefix];
    allParts.push(...parts);
    return allParts.join("...");
  }

  private get metaKey() {
    return this.getKey(this.options.metaKey);
  }

  getKeyByIncompleteArtifact(artifact: IncompleteArtifact) {
    return this.getKey("incomplete", artifact.name, artifact.namespace);
  }

  getKeyById(id: number) {
    return this.getKey("id", `${id}`);
  }

  get map(): IArtifactMap {
    return this.localMap;
  }
}

type BatchResult = EventWeakRef;

export type RedisClientFactory = () => Promise<RedisClient>;

export class BatchEventRecorder implements IEventRecorder {
  private eventQueue: Array<IRecorderEvent>;
  private options: BatchEventRecorderOptions;
  private dataSource: DataSource;
  private dataSourcePool: DataSource[];
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
  private preCommitCount: number;
  private _preCommitTableName: string;
  private isPreCommitTableOpen: boolean;
  private committing: boolean;
  private redis: RedisClient;
  private redisFactory: RedisClientFactory;
  private artifactResolver: ArtifactResolver;
  private commitResult: ICommitResult | null;

  constructor(
    dataSource: DataSource,
    dataSourcePool: DataSource[],
    recordingRepository: Repository<Recording>,
    eventTypeRepository: Repository<EventType>,
    redisFactory: RedisClientFactory,
    options?: Partial<BatchEventRecorderOptions>,
  ) {
    this.dataSourcePool = dataSourcePool;
    this.dataSource = dataSource;
    this.recordingRepository = recordingRepository;
    this.eventTypeRepository = eventTypeRepository;
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
    this.redisFactory = redisFactory;
    this.preCommitCount = 0;
    this.commitResult = null;

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

    this.redis = await this.redisFactory();

    this.artifactResolver = new ArtifactResolver(this.dataSource, this.redis, {
      maxBatchSize: this.options.maxBatchSize,
    });

    await this.loadArtifacts();

    if (this.isPreCommitTableOpen) {
      throw new RecorderError("Only one temporary table may be set at a time");
    }

    // Create a temporary table to collect precommit events
    const formattedRecorderId = this.recorderId.replace(/-/g, "_");
    this._preCommitTableName = `recorder_pre_commit_${formattedRecorderId}_${this.tableCounter}`;
    this.tableCounter += 1;
    this.isPreCommitTableOpen = true;
    this.preCommitCount = 0;
    this.commitResult = new CommitResult();

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

  async rollback(): Promise<void> {
    if (this.isPreCommitTableOpen) {
      await this.clean();
    }
  }

  private async clean() {
    logger.debug("dropping the temporary table");
    const tmDropTable = timer("drop table");
    this.commitResult = null;

    await this.dataSource.query(`
      DROP TABLE ${this.preCommitTableName}
    `);
    try {
      await this.redis.del(this.preCommitTableName);
    } catch (err) {
      logger.error("error attempting to delete the redis set");
      logger.error(err);
    }
    tmDropTable();

    this._preCommitTableName = "";
    this.isPreCommitTableOpen = false;
    this.committing = false;
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

    logger.debug("flush complete. beginning recorder commit");

    // Using the recorder_temp_event table we can commit all of the events
    // Remove anything with duplicates
    const tmDelDupes = timer("delete event dupes");
    const commitResult = this.commitResult!;
    const toIdsToResolve: number[] = [];
    try {
      const invalid = (await this.dataSource.query(`
        WITH events_with_duplicates AS (
          SELECT 
            pct."sourceId",
            pct."typeId",
            pct."toId",
            COUNT(*) as "count"
          FROM ${this.preCommitTableName} AS pct
          GROUP BY 1,2,3
          HAVING COUNT(*) > 1
        ), deleted_events AS (
          DELETE FROM ${this.preCommitTableName} p
          USING events_with_duplicates ewd
          WHERE p."sourceId" = ewd."sourceId" AND
                p."typeId" = ewd."typeId" AND
                p."toId" = ewd."toId" AND
                ewd."typeId" IS NOT NULL AND
                ewd."sourceId" IS NOT NULL AND
                ewd."toId" IS NOT NULL
          RETURNING p."sourceId", p."typeId", p."toId", p."time", p."fromId", p."amount", p."details"
        )
        INSERT INTO ${this.preCommitTableName} ("sourceId", "typeId", "toId", "time", "fromId", "amount", "details")
        SELECT 
          DISTINCT ON ("sourceId", "typeId", "toId")
          d."sourceId",
          d."typeId",
          d."toId",
          d."time",
          d."fromId",
          d."amount",
          d."details"
        FROM deleted_events d
        RETURNING "sourceId", "typeId", "toId"
      `)) as { sourceId: string; typeId: number; toId: number }[];
      tmDelDupes();
      logger.debug(`merged ${invalid.length} events of duplicates`);

      const eventsToCommitCount = this.preCommitCount - invalid.length;

      logger.debug(
        `committing ${eventsToCommitCount} events to event database`,
      );
      // Write back into the main database

      if (this.recorderOptions.overwriteExistingEvents) {
        logger.debug(`removing existing events`);
        // Delete existing events
        const tmDelEvents = timer("delete existing events");
        await this.dataSource.query(
          `
            DELETE FROM event e
            USING ${this.preCommitTableName} p
            WHERE p."sourceId" = e."sourceId" AND
                  p."typeId" = e."typeId" AND
                  p."toId" = e."toId"
          `,
        );
        tmDelEvents();
      }

      const tmCommitEvents = timer("commit to event table");
      const pool = [this.dataSource];
      pool.push(...this.dataSourcePool);

      const limitSize = Math.round(eventsToCommitCount / pool.length);

      const concurrent = pool.reduce<Promise<BatchResult[]>[]>((a, ds, i) => {
        const offset = i * limitSize;

        const result = async () => {
          const written = (await ds.query(`
            INSERT INTO event ("sourceId", "typeId", "time", "toId", "fromId", "amount", "details")
            SELECT 
              "sourceId", 
              "typeId", 
              "time", 
              "toId", 
              "fromId", 
              "amount", 
              "details" 
            FROM ${this.preCommitTableName}
            OFFSET ${offset}
            LIMIT ${limitSize}
            ON CONFLICT ("sourceId", "typeId", "time", "toId") DO NOTHING

            RETURNING "sourceId", "typeId", "toId"
          `)) as BatchResult[];

          const writtenIds = written.map((w) => {
            toIdsToResolve.push(w.toId);
            return dbEventUniqueId({
              sourceId: w.sourceId,
              typeId: w.typeId,
              toId: w.toId,
            });
          });

          if (writtenIds.length > 0) {
            await this.redis.sRem(this.preCommitTableName, writtenIds);
          }
          return written;
        };
        a.push(result());
        return a;
      }, []);

      const results = await Promise.all(concurrent);
      const committedRefs = results.reduce<BatchResult[]>((a, c) => {
        // Don't use the spread operator `...` or we may experience call stack
        // overflows.
        c.forEach((r) => {
          return a.push(r);
        });

        return a;
      }, []);

      // Check redis for the skipped values
      const skippedRedisMembers = await this.redis.sMembers(
        this.preCommitTableName,
      );
      const skippedRefs = skippedRedisMembers.map((s) => {
        return splitDbEventUniqueId(s);
      });
      logger.debug("skipped refs %d", skippedRefs.length);

      tmCommitEvents();

      const uncommittedEvents = new UniqueArray<RecorderEventRef>(
        eventUniqueId,
      );

      const artifactMap = this.artifactResolver.map;
      const convertBatch = async (weakRefs: EventWeakRef[]) => {
        const events: RecorderEventRef[] = [];
        for (const ref of weakRefs) {
          const artifact = await artifactMap.getIncomplete(ref.toId);
          const t = RecorderEventType.fromDBEventType(
            this.eventTypeIdMap[ref.typeId],
          );
          events.push({
            sourceId: ref.sourceId,
            to: artifact,
            type: t,
          });
        }
        return events;
      };

      const committedEvents = await asyncBatchFlattened(
        committedRefs,
        this.options.maxBatchSize,
        convertBatch,
      );
      const skippedEvents = await asyncBatchFlattened(
        skippedRefs,
        this.options.maxBatchSize,
        convertBatch,
      );
      const invalidEvents = await asyncBatchFlattened(
        invalid,
        this.options.maxBatchSize,
        convertBatch,
      );
      invalidEvents.forEach((e) => {
        uncommittedEvents.push(e);
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
      committedEvents.forEach((e) => {
        commitResult.committed.push(eventUniqueId(e));
      });
      skippedEvents.forEach((e) => {
        commitResult.skipped.push(eventUniqueId(e));
      });
    } catch (err) {
      logger.error(`error during commit`);
      logger.error(`err=${JSON.stringify(err)}`);
      this.emitter.emit("commit-error", err);
      throw new RecorderError("commit error. failed to commit properly");
    }
    await this.clean();
    return commitResult;
  }

  async loadArtifacts() {
    return this.artifactResolver.loadArtifacts();
  }

  private incompleteArtifactRedisKey(artifact: IncompleteArtifact) {
    return `artifact::${artifact.name}::${artifact.namespace}`;
  }

  private async getArtifactId(artifact: IncompleteArtifact) {
    const res = await this.redis.get(this.incompleteArtifactRedisKey(artifact));
    if (!res) {
      return null;
    }
    return parseInt(res);
  }

  private async matchArtifactIds(artifacts: IncompleteArtifact[]) {
    const res = await this.artifactResolver.map.resolveToIds(artifacts);
    const matches = artifacts.map((a, i) => {
      const id: number | null = res[i];
      return [a, id] as [IncompleteArtifact, number | null];
    });
    return matches;
  }

  private async matchArtifactIdsOrFail(
    artifacts: IncompleteArtifact[],
  ): Promise<ArtifactMatches> {
    const matches = await this.matchArtifactIds(artifacts);
    const nulls = matches.filter((m) => {
      return m[1] === null;
    });
    if (nulls.length > 0) {
      // Log for debugging purposes
      nulls.forEach((n) => {
        logger.debug(
          `missing artifactId for Artifact[name=${n[0].name}, namespace=${n[0].namespace}]`,
        );
      });
      throw new RecorderError(`missing ${nulls.length} artifact ids`);
    }
    return matches;
  }

  private async uniqArtifactsFromEvents(events: IRecorderEvent[]) {
    const determineUniqArtifactsTimers = timer("deteremine unique artifacts");
    const uniqArtifacts = new UniqueArray<IncompleteArtifact>((a) => {
      return `${a.name}:${a.namespace}`;
    });

    for (const event of events) {
      const toId: number | null = null;
      const fromId: number | null = null;

      if (!toId) {
        uniqArtifacts.push(event.to);
      }

      if (event.from) {
        if (!fromId) {
          uniqArtifacts.push(event.from);
        }
      }
    }
    const matches = await this.matchArtifactIds(uniqArtifacts.items());
    const newArtifacts = matches.reduce<IncompleteArtifact[]>((a, c) => {
      if (c[1] === null) {
        a.push(c[0]);
      }
      return a;
    }, []);
    determineUniqArtifactsTimers();
    return [uniqArtifacts.items(), newArtifacts];
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
    logger.debug(`processing ${processing.length} events`);

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
        console.log("%j", event);
        this.commitResult!.skipped.push(eventUniqueId(event));
        this.notifySuccess([event]);
        continue;
      }
      newEvents.push(event);
    }

    // Get all of the unique artifacts
    const [allArtifacts, newArtifacts] = await this.uniqArtifactsFromEvents(
      newEvents,
    );

    const writeArtifacts = async () => {
      const tmWriteArtifacts = timer("writing new artifacts");
      if (newArtifacts.length > 0) {
        const artifactResponse = (await this.dataSource.query(
          `
            INSERT INTO artifact("name", "namespace", "type", "url")
            SELECT * FROM unnest(
              $1::text[], $2::artifact_namespace_enum[], $3::artifact_type_enum[], $4::text[]
            ) 
            ON CONFLICT ("name", "namespace") DO NOTHING
            RETURNING "name", "namespace", "id"
          `,
          newArtifacts.reduce<
            [string[], string[], string[], (string | null)[]]
          >(
            (a, c) => {
              a[0].push(c.name);
              a[1].push(c.namespace);
              a[2].push(c.type);
              a[3].push(c.url || null);
              return a;
            },
            [[], [], [], []],
          ),
        )) as { name: string; namespace: string; id: number }[];
        tmWriteArtifacts();
        logger.debug(`added ${artifactResponse.length} new artifacts`);
      }
    };

    try {
      await this.retryDbCall(writeArtifacts);
    } catch (err) {
      logger.error("encountered an error writing to the artifacts table");
      logger.debug(typeof err);
      logger.error(`Error type=${typeof err}`);
      //logger.error(`Error as JSON=${JSON.stringify(err)}`);
      logger.error(err);
      this.notifyFailure(newEvents, err);
      this.emitter.emit("error", err);
    }

    const loadArtifactIdsTimers = timer(
      `load ${allArtifacts.length} artifact ids for current flush`,
    );
    await this.loadArtifacts();
    loadArtifactIdsTimers();

    const dbEvents = await this.createEventsFromRecorderEvents(
      batchId,
      newEvents,
    );

    const precommitWrites = async () => {
      const precommitTimer = timer("write to precommit table");
      const pgWrite = this.dataSource.query(
        `
          INSERT INTO ${this.preCommitTableName}
            (
              "sourceId", "typeId", "time", 
              "toId", "fromId", "amount", "details"
            )
            (
              select * from unnest(
                $1::text[], $2::int[], $3::timestamptz[],
                $4::int[],
                $5::int[],
                $6::float[], $7::jsonb[]
              )
            )
          RETURNING "id"
        `,
        [
          dbEvents.sourceIds,
          dbEvents.typeIds,
          dbEvents.times,
          dbEvents.toIds,
          dbEvents.fromIds,
          dbEvents.amounts,
          dbEvents.details,
        ],
      );
      await this.redis.sAdd(this.preCommitTableName, dbEvents.uniqueIds);
      const res = (await pgWrite) as { id: number }[];
      precommitTimer();
      return res;
    };

    // Insert events into the pre commit event table
    try {
      const result = await this.retryDbCall(precommitWrites);
      if (result.length !== newEvents.length) {
        throw new RecorderError(
          `recorder writes failed. Expected ${newEvents.length} writes but only received ${result.length}`,
        );
      }
      this.preCommitCount += result.length;
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

  protected async createEventsFromRecorderEvents(
    batchId: number,
    recorderEvents: IRecorderEvent[],
  ): Promise<PGRecorderTempEventBatchInput> {
    const inputs: PGRecorderTempEventBatchInput = {
      sourceIds: [],
      typeIds: [],
      times: [],
      toIds: [],
      fromIds: [],
      amounts: [],
      details: [],
      uniqueIds: [],
    };
    const toArtifacts: IncompleteArtifact[] = [];
    const fromArtifacts: (IncompleteArtifact | null)[] = [];
    for (const e of recorderEvents) {
      const eventType = this.resolveEventType(e.type);
      toArtifacts.push(e.to);

      if (e.from) {
        fromArtifacts.push(e.from);
      }

      inputs.sourceIds.push(e.sourceId);
      inputs.typeIds.push(eventType.id.valueOf());
      inputs.times.push(e.time.toJSDate());
      inputs.amounts.push(e.amount);
      inputs.details.push(e.details);
      //{ sourceId: e.sourceId, typeId: eventType.id.valueOf(), toId }));
    }
    inputs.toIds = (await this.artifactResolver.map.resolveToIds(
      toArtifacts,
    )) as number[];
    inputs.fromIds = await this.artifactResolver.map.resolveToIds(
      fromArtifacts,
    );

    inputs.toIds.forEach((toId, i) => {
      inputs.uniqueIds.push(
        dbEventUniqueId({
          sourceId: inputs.sourceIds[i],
          typeId: inputs.typeIds[i],
          toId: toId,
        }),
      );
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
