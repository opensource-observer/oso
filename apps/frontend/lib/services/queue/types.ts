export interface QueueResult {
  success: boolean;
  messageId?: string;
  error?: QueueError;
}

export class QueueError extends Error {
  constructor(
    message: string,
    public readonly code: QueueErrorCode,
    public readonly cause?: Error,
  ) {
    super(message);
    this.name = "QueueError";
  }
}

export enum QueueErrorCode {
  SERIALIZATION_ERROR = "SERIALIZATION_ERROR",
  PUBLISH_ERROR = "PUBLISH_ERROR",
  TOPIC_NOT_FOUND = "TOPIC_NOT_FOUND",
  CONFIGURATION_ERROR = "CONFIGURATION_ERROR",
}

export interface QueueConfig {
  projectId: string;
  emulatorHost?: string;
}

export type MessageType = "data-model";

export interface ProtobufMessage {
  runId: Uint8Array;
}

export interface ProtobufEncoder<T> {
  encode(message: T): { finish(): Uint8Array };
  toJSON(message: T): unknown;
}

interface IQueueServiceBase {
  close(): Promise<void>;
}

interface IDataModelRunQueueService {
  publishDataModelRun<Q extends ProtobufMessage>(
    request: Q,
    encoder: ProtobufEncoder<Q>,
  ): Promise<QueueResult>;
}

export interface IQueueService
  extends IQueueServiceBase,
    IDataModelRunQueueService {
  // & IStaticModelRunQueueService
  // & IDataIngestionQueueService
}
