import { EventEmitter } from "node:events";
import {
  IEventRecorderClient,
  IEventGroupRecorder,
  IncompleteEvent,
  IncompleteArtifact,
  RecordHandle,
} from "./types.js";

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
  }

  async record(event: IncompleteEvent): Promise<void> {
    const group = this.grouperFn(event);
    const promises = this.getGroupRecordHandles(group);
    promises.push(await this.recorder.record(event));
  }

  private getGroupRecordHandles(group: T): RecordHandle[] {
    const id = this.groupToStrFn(group);
    if (!this.groupRecordHandles[id]) {
      this.groupRecordHandles[id] = [];
    }
    return this.groupRecordHandles[id];
  }

  handlesForGroup(group: T): RecordHandle[] {
    const id = this.groupToStrFn(group);
    return this.groupRecordHandles[id];
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
