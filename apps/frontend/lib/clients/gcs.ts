import { GetSignedUrlConfig, Storage } from "@google-cloud/storage";
import { GCP_CREDENTIALS_JSON_B64, GOOGLE_PROJECT_ID } from "@/lib/config";

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

export async function fileExists(
  bucketName: string,
  fileName: string,
): Promise<boolean> {
  const storage = getStorage();
  const file = storage.bucket(bucketName).file(fileName);
  const [exists] = await file.exists();
  return exists;
}

export async function copyFile(
  source: { bucketName: string; fileName: string },
  destination: { bucketName: string; fileName: string },
) {
  const storage = getStorage();
  return storage
    .bucket(source.bucketName)
    .file(source.fileName)
    .copy(storage.bucket(destination.bucketName).file(destination.fileName));
}

export function parseGcsUrl(
  gcsUrl: string,
): { bucketName: string; fileName: string } | null {
  const match = gcsUrl.match(/^gs:\/\/([^/]+)\/(.+)$/);
  if (!match) return null;
  return {
    bucketName: match[1],
    fileName: match[2],
  };
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
