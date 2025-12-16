import { GetSignedUrlConfig, Storage } from "@google-cloud/storage";
import { GOOGLE_PROJECT_ID, GCP_CREDENTIALS_JSON_B64 } from "@/lib/config";

// Initialize storage client
let storage: Storage | null = null;

function getStorage() {
  if (storage) return storage;

  const credentials = GCP_CREDENTIALS_JSON_B64
    ? JSON.parse(
        Buffer.from(GCP_CREDENTIALS_JSON_B64, "base64").toString("utf-8"),
      )
    : undefined;

  storage = new Storage({
    projectId: GOOGLE_PROJECT_ID,
    credentials,
  });
  return storage;
}

export async function getSignedUrl(
  bucketName: string,
  fileName: string,
  expirationMinutes: number = 15,
): Promise<string> {
  const storage = getStorage();
  const options: GetSignedUrlConfig = {
    version: "v4" as const,
    action: "read" as const,
    expires: Date.now() + expirationMinutes * 60 * 1000,
  };

  const [url] = await storage
    .bucket(bucketName)
    .file(fileName)
    .getSignedUrl(options);

  return url;
}
