import { QueueService } from "@/lib/services/queue/queue-service";
import { QueueConfig } from "@/lib/services/queue/types";
import {
  GCP_CREDENTIALS_JSON_B64,
  GOOGLE_PROJECT_ID,
  PUBSUB_EMULATOR_HOST,
} from "@/lib/config";

export function createQueueService(
  config?: Partial<QueueConfig>,
): QueueService {
  return new QueueService({
    projectId: config?.projectId ?? GOOGLE_PROJECT_ID,
    emulatorHost: config?.emulatorHost ?? PUBSUB_EMULATOR_HOST,
    gcpCredentialsJsonB64:
      config?.gcpCredentialsJsonB64 ?? GCP_CREDENTIALS_JSON_B64,
  });
}
