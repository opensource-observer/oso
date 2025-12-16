import { QueueService } from "@/lib/services/queue/queue-service";
import { QueueConfig } from "@/lib/services/queue/types";
import {
  GCP_CREDENTIALS_JSON,
  GOOGLE_PROJECT_ID,
  PUBSUB_EMULATOR_HOST,
} from "@/lib/config";

export function createQueueService(
  config?: Partial<QueueConfig>,
): QueueService {
  return new QueueService({
    projectId: config?.projectId ?? GOOGLE_PROJECT_ID,
    emulatorHost: config?.emulatorHost ?? PUBSUB_EMULATOR_HOST,
    gcpCredentialsJson: config?.gcpCredentialsJson ?? GCP_CREDENTIALS_JSON,
  });
}
