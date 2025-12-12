import { PubSubClient } from "@/lib/services/queue/pubsub-client";
import {
  IQueueService,
  PublishMessageOptions,
  ProtobufMessage,
  QueueConfig,
  QueueError,
  QueueErrorCode,
  QueueResult,
} from "@/lib/services/queue/types";
import { logger } from "@/lib/logger";

export class QueueService implements IQueueService {
  private client: PubSubClient;

  constructor(config: QueueConfig) {
    this.client = new PubSubClient(config);
  }

  async queueMessage<Q extends ProtobufMessage>({
    queueName,
    message,
    encoder,
  }: PublishMessageOptions<Q>): Promise<QueueResult> {
    const topicName = this.getTopicName(queueName);

    try {
      const binaryData = encoder.encode(message).finish();
      const jsonData = encoder.toJSON(message);

      const messageId = await this.client.publishMessage(
        topicName,
        binaryData,
        jsonData,
        {
          timestamp: new Date().toISOString(),
        },
      );

      logger.info(`Published Message to ${topicName}`, {
        messageId,
        runId: Buffer.from(message.runId).toString("hex"),
      });

      return { success: true, messageId };
    } catch (error) {
      logger.error(`Failed to publish message to ${topicName}`, {
        error,
        topicName,
      });

      return {
        success: false,
        error:
          error instanceof QueueError
            ? error
            : new QueueError(
                "Unknown error during publish",
                QueueErrorCode.PUBLISH_ERROR,
                error as Error,
              ),
      };
    }
  }

  private getTopicName(queueName: string): string {
    return queueName;
  }

  async close(): Promise<void> {
    await this.client.close();
  }
}
