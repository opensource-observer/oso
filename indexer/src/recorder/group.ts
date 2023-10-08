import { EventEmitter } from "node:events";
import {
  IEventRecorder,
  IEventGroupRecorder,
  IncompleteEvent,
  RecordResponse,
  EventGroupRecorderCallback,
  IncompleteArtifact,
} from "./types.js";
import { AsyncResults } from "../utils/async-results.js";
import { collectAsyncResults } from "../utils/async-results.js";

export type EventGrouperFn<T> = (event: IncompleteEvent) => T;
export type GroupObjToStrFn<T> = (group: T) => string;

/**
 * Allows for organizing a large set of pending events for specific groups
 * (usually artifacts)
 */
export class EventGroupRecorder<T> implements IEventGroupRecorder<T> {
  private groupRecordPromises: Record<string, Promise<RecordResponse>[]>;
  private grouperFn: EventGrouperFn<T>;
  private groupToStrFn: GroupObjToStrFn<T>;
  private emitter: EventEmitter;
  private recorder: IEventRecorder;
  private committed: boolean;
  private listeningIds: Record<string, boolean>;

  constructor(
    recorder: IEventRecorder,
    grouperFn: EventGrouperFn<T>,
    groupObjToStrFn: GroupObjToStrFn<T>,
  ) {
    this.groupRecordPromises = {};
    this.grouperFn = grouperFn;
    this.groupToStrFn = groupObjToStrFn;
    this.emitter = new EventEmitter();
    this.recorder = recorder;
    this.listeningIds = {};

    this.committed = false;
  }

  commit(): void {
    if (this.committed) {
      return;
    }
    // This should only run once.
    this.committed = true;

    setImmediate(() => {
      for (const groupId in this.groupRecordPromises) {
        // Catch errors so we can record all of them
        this.commitId(groupId);
      }
    });
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

  record(event: IncompleteEvent): void {
    const group = this.grouperFn(event);
    const promises = this.getGroupRecordPromises(group);
    promises.push(this.recorder.record(event));
  }

  private commitId(id: string): void {
    const promises = this.groupRecordPromises[id] || [];
    collectAsyncResults(promises)
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

  private getGroupRecordPromises(group: T): Promise<RecordResponse>[] {
    const id = this.groupToStrFn(group);
    if (!this.groupRecordPromises[id]) {
      this.groupRecordPromises[id] = [];
    }
    return this.groupRecordPromises[id];
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
}

export class ArtifactGroupRecorder extends EventGroupRecorder<IncompleteArtifact> {
  constructor(recorder: IEventRecorder) {
    const artifactToString = (a: IncompleteArtifact) => {
      return `${a.name}:${a.namespace}:${a.type}`;
    };
    super(recorder, (event) => event.to, artifactToString);
  }
}
