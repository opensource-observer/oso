import { PubSubClient } from "@/lib/services/queue/pubsub-client";
import {
  QueueConfig,
  QueueError,
  QueueErrorCode,
  QueueResult,
} from "@/lib/services/queue/types";
import { DataModelRunRequest } from "@/lib/proto/generated/data-model";
import { logger } from "@/lib/logger";
import { NODE_ENV } from "@/lib/config";

export class QueueService {
  private client: PubSubClient;

  constructor(config: QueueConfig) {
    this.client = new PubSubClient(config);
  }

  async publishDataModelRun(
    request: DataModelRunRequest,
  ): Promise<QueueResult> {
    const topicName = this.getTopicName("data-model");

    try {
      const encoded = DataModelRunRequest.encode(request).finish();
      const data = Buffer.from(encoded);

      const messageId = await this.client.publishMessage(topicName, data, {
        messageType: "DataModelRunRequest",
        timestamp: new Date().toISOString(),
      });

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
