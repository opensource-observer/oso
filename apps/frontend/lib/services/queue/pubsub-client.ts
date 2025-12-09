import { PubSub, Topic } from "@google-cloud/pubsub";
import { logger } from "@/lib/logger";
import {
  QueueConfig,
  QueueError,
  QueueErrorCode,
} from "@/lib/services/queue/types";

export class PubSubClient {
  private client: PubSub;
  private topics: Map<string, Topic> = new Map();

  constructor(config: QueueConfig) {
    const clientConfig: any = {
      projectId: config.projectId,
    };

    if (config.emulatorHost) {
      logger.info(`Using Pub/Sub emulator at ${config.emulatorHost}`);
      clientConfig.apiEndpoint = config.emulatorHost;
    }

    this.client = new PubSub(clientConfig);
  }

  async getTopic(topicName: string): Promise<Topic> {
    if (this.topics.has(topicName)) {
      return this.topics.get(topicName)!;
    }

    const topic = this.client.topic(topicName);
    const [exists] = await topic.exists();

    if (!exists) {
      throw new QueueError(
        `Topic ${topicName} does not exist`,
        QueueErrorCode.TOPIC_NOT_FOUND,
      );
    }

    this.topics.set(topicName, topic);
    return topic;
  }

  async publishMessage(
    topicName: string,
    data: Buffer,
    attributes?: Record<string, string>,
  ): Promise<string> {
    try {
      const topic = await this.getTopic(topicName);
      const messageId = await topic.publishMessage({ data, attributes });
      return messageId;
    } catch (error) {
      if (error instanceof QueueError) {
        throw error;
      }
      throw new QueueError(
        `Failed to publish message to ${topicName}`,
        QueueErrorCode.PUBLISH_ERROR,
        error as Error,
      );
    }
  }

  async close(): Promise<void> {
    await this.client.close();
  }
}
