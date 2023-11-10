import { EventEmitter } from "node:events";
import {
  IEventRecorderClient,
  IEventGroupRecorder,
  IncompleteEvent,
  EventGroupRecorderCallback,
  IncompleteArtifact,
  RecordHandle,
} from "./types.js";
import { AsyncResults } from "../utils/async-results.js";
import { randomUUID } from "node:crypto";
import { logger } from "../utils/logger.js";

export type EventGrouperFn<T> = (event: IncompleteEvent) => T;
export type GroupObjToStrFn<T> = (group: T) => string;

/**
 * Allows for organizing a large set of pending events for specific groups
 * (usually artifacts)
 */
export class EventGroupRecorder<T> implements IEventGroupRecorder<T> {
  private groupRecordHandles: Record<string, RecordHandle[]>;
  private grouperFn: EventGrouperFn<T>;
  private groupToStrFn: GroupObjToStrFn<T>;
  private emitter: EventEmitter;
  private recorder: IEventRecorderClient;
  private committed: boolean;
  private listeningIds: Record<string, boolean>;
  private objectId: string;

  constructor(
    recorder: IEventRecorderClient,
    grouperFn: EventGrouperFn<T>,
    groupObjToStrFn: GroupObjToStrFn<T>,
  ) {
    this.groupRecordHandles = {};
    this.grouperFn = grouperFn;
    this.groupToStrFn = groupObjToStrFn;
    this.emitter = new EventEmitter();
    this.recorder = recorder;
    this.listeningIds = {};
    this.objectId = randomUUID();
    this.committed = false;
  }

  commit(): void {
    if (this.committed) {
      return;
    }
    // This should only run once.
    this.committed = true;

    setTimeout(() => {
      for (const groupId in this.listeningIds) {
        // Catch errors so we can record all of them
        this.commitId(groupId).catch((err) => {
          logger.error(
            `error encountered in artifact commit with groupId=${groupId}`,
          );
          this.emitter.emit("error", err);
        });
      }
    }, 100);
  }

  async wait(group: T): Promise<AsyncResults<string>> {
    return new Promise((resolve) => {
      const cb: EventGroupRecorderCallback<string> = (results) => {
        resolve(results);
        this.removeGroupCallback(group, cb);
      };
      this.addGroupCallback(group, cb);
    });
  }

  async record(event: IncompleteEvent): Promise<void> {
    const group = this.grouperFn(event);
    const promises = this.getGroupRecordHandles(group);
    promises.push(await this.recorder.record(event));
  }

  private commitId(id: string): Promise<void> {
    logger.debug(`commiting group ${id}`);
    const recordHandles = this.groupRecordHandles[id] || [];
    return this.recorder
      .wait(recordHandles)
      .then((result) => {
        this.emitter.emit(id, result);
      })
      .catch((err) => {
        // This is a final catch all here just in case. This shouldn't
        // actually have to happen unless something is really wrong.
        this.emitter.emit(id, {
          errors: [err],
          success: [],
        });
      });
  }

  private getGroupRecordHandles(group: T): RecordHandle[] {
    const id = this.groupToStrFn(group);
    if (!this.groupRecordHandles[id]) {
      this.groupRecordHandles[id] = [];
    }
    return this.groupRecordHandles[id];
  }

  private addGroupCallback(
    group: T,
    cb: EventGroupRecorderCallback<string>,
  ): void {
    const id = this.groupToStrFn(group);
    this.listeningIds[id] = true;
    this.emitter.addListener(id, cb);
  }

  private removeGroupCallback(
    group: T,
    cb: EventGroupRecorderCallback<string>,
  ): void {
    const id = this.groupToStrFn(group);
    delete this.listeningIds[id];
    this.emitter.removeListener(id, cb);
  }

  addListener(
    message: "error" | "group-completed",
    cb: (...args: any) => void,
  ): EventEmitter {
    return this.emitter.addListener(message, cb);
  }

  removeListener(
    message: "error" | "group-completed",
    cb: (...args: any) => void,
  ) {
    return this.emitter.removeListener(message, cb);
  }
}

export class ArtifactGroupRecorder extends EventGroupRecorder<IncompleteArtifact> {
  constructor(recorder: IEventRecorderClient) {
    const artifactToString = (a: IncompleteArtifact) => {
      return `${a.name}:${a.namespace}:${a.type}`;
    };
    super(recorder, (event) => event.to, artifactToString);
  }
}
