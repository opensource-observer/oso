import {
  ClientConfig,
  Encodings,
  PubSub,
  SchemaEncoding,
  Topic,
} from "@google-cloud/pubsub";
import { google } from "@google-cloud/pubsub/build/protos/protos";
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
    const clientConfig: ClientConfig = {
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
    binaryData: Uint8Array,
    jsonData: unknown,
    attributes?: Record<string, string>,
  ): Promise<string> {
    try {
      const topic = await this.getTopic(topicName);
      const [metadata] = await topic.getMetadata();
      const encoding = metadata.schemaSettings?.encoding;
      const data = this.encodeMessageData(encoding, binaryData, jsonData);

      return await topic.publishMessage({ data, attributes });
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

  private encodeMessageData(
    encoding: SchemaEncoding | google.pubsub.v1.Encoding | null | undefined,
    binaryData: Uint8Array,
    jsonData: unknown,
  ): Buffer {
    const normalizedEncoding = this.normalizeEncoding(encoding);

    if (!normalizedEncoding || normalizedEncoding === Encodings.Binary) {
      return Buffer.from(binaryData);
    }

    if (normalizedEncoding === Encodings.Json) {
      return Buffer.from(JSON.stringify(jsonData));
    }

    throw new QueueError(
      `Unknown schema encoding: ${normalizedEncoding}`,
      QueueErrorCode.CONFIGURATION_ERROR,
    );
  }

  private normalizeEncoding(
    encoding: SchemaEncoding | google.pubsub.v1.Encoding | null | undefined,
  ): SchemaEncoding | null | undefined {
    if (encoding == null || typeof encoding === "string") {
      return encoding;
    }

    if (encoding === google.pubsub.v1.Encoding.BINARY) return Encodings.Binary;
    if (encoding === google.pubsub.v1.Encoding.JSON) return Encodings.Json;

    return undefined;
  }

  async close(): Promise<void> {
    await this.client.close();
  }
}
