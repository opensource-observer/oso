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
