import { PubSubClient } from "@/lib/services/queue/pubsub-client";
import {
  IQueueService,
  ProtobufEncoder,
  ProtobufMessage,
  QueueConfig,
  QueueError,
  QueueErrorCode,
  QueueResult,
} from "@/lib/services/queue/types";
import {
  DATA_MODEL_MESSAGE_TYPE,
  DATA_MODEL_TOPIC_KEY,
} from "@/lib/services/queue/constants";
import { logger } from "@/lib/logger";
import { NODE_ENV } from "@/lib/config";

export class QueueService implements IQueueService {
  private client: PubSubClient;

  constructor(config: QueueConfig) {
    this.client = new PubSubClient(config);
  }

  async publishDataModelRun<Q extends ProtobufMessage>(
    request: Q,
    encoder: ProtobufEncoder<Q>,
  ): Promise<QueueResult> {
    const topicName = this.getTopicName(DATA_MODEL_TOPIC_KEY);

    try {
      const binaryData = encoder.encode(request).finish();
      const jsonData = encoder.toJSON(request);

      const messageId = await this.client.publishMessage(
        topicName,
        binaryData,
        jsonData,
        {
          messageType: DATA_MODEL_MESSAGE_TYPE,
          timestamp: new Date().toISOString(),
        },
      );

      logger.info(`Published DataModelRunRequest to ${topicName}`, {
        messageId,
        runId: Buffer.from(request.runId).toString("hex"),
      });

      return { success: true, messageId };
    } catch (error) {
      logger.error(`Failed to publish DataModelRunRequest`, {
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

  private getTopicName(messageType: string): string {
    const env = NODE_ENV === "production" ? "production" : "staging";
    return `oso-${env}-${messageType}-tasks`;
  }

  async close(): Promise<void> {
    await this.client.close();
  }
}
