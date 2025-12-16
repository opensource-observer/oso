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
  gcpCredentialsJson?: string;
}

export type MessageType = "data-model";

export interface ProtobufMessage {
  runId: Uint8Array;
}

export interface ProtobufEncoder<T> {
  encode(message: T): { finish(): Uint8Array };
  toJSON(message: T): unknown;
}

export type PublishMessageOptions<Q extends ProtobufMessage> = {
  queueName: string;
  message: Q;
  encoder: ProtobufEncoder<Q>;
};

export interface IQueueService {
  close(): Promise<void>;
  queueMessage<Q extends ProtobufMessage>(
    options: PublishMessageOptions<Q>,
  ): Promise<QueueResult>;
}
