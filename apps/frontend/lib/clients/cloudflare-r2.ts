import {
  S3Client,
  GetObjectCommand,
  CreateMultipartUploadCommand,
  CompleteMultipartUploadCommand,
  UploadPartCommand,
  CompletedPart,
  CopyObjectCommand,
  CreateBucketCommand,
  HeadBucketCommand,
  PutBucketLifecycleConfigurationCommand,
  NotFound,
  PutObjectCommand,
  HeadObjectCommand,
} from "@aws-sdk/client-s3";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner";
import { createHash } from "node:crypto";
import {
  CLOUDFLARE_R2_ENDPOINT,
  CLOUDFLARE_R2_ACCESS_KEY_ID,
  CLOUDFLARE_R2_SECRET_ACCESS_KEY,
} from "@/lib/config";
import { assert } from "@opensource-observer/utils";
import { logger } from "@/lib/logger";

const PART_SIZE = 10 * 1024 * 1024; // 10MB

type ObjectLocation = {
  bucketName: string;
  objectKey: string;
};

const S3 = new S3Client({
  region: "auto",
  endpoint: CLOUDFLARE_R2_ENDPOINT,
  credentials: {
    accessKeyId: CLOUDFLARE_R2_ACCESS_KEY_ID,
    secretAccessKey: CLOUDFLARE_R2_SECRET_ACCESS_KEY,
  },
});

function queryToKey(queryBody: any): string {
  const queryStr = JSON.stringify(queryBody);
  const normalized = queryStr.toLowerCase().trim();
  const buffer = Buffer.from(normalized, "utf-8");
  const hash = createHash("md5").update(buffer).digest("hex");
  return hash;
}

async function getObjectByQuery(orgName: string, queryBody: any) {
  const key = queryToKey(queryBody);
  return getObject({ bucketName: orgName, objectKey: key });
}

async function putObjectByQuery(
  orgName: string,
  queryBody: any,
  body: ReadableStream,
) {
  const key = queryToKey(queryBody);
  return putObject({ bucketName: orgName, objectKey: key }, body);
}

async function getObject(loc: ObjectLocation) {
  const command = new GetObjectCommand({
    Bucket: loc.bucketName,
    Key: loc.objectKey,
  });
  const response = await S3.send(command);
  return response;
}

async function putObject(loc: ObjectLocation, body: ReadableStream) {
  // https://developers.cloudflare.com/r2/objects/multipart-objects/
  // Part sizes must be at least 5 MB in size, except for the last part.
  // Part sizes must be less than 5 GB
  // Part sizes must be the same size except for the last part
  const createCommand = new CreateMultipartUploadCommand({
    Bucket: loc.bucketName,
    Key: loc.objectKey,
  });
  const createResponse = await S3.send(createCommand);
  const uploadId = createResponse.UploadId;

  if (!uploadId) {
    throw new Error("Failed to create multipart upload");
  }

  const reader = body.getReader();
  const partETags: CompletedPart[] = [];
  const buffer = new Uint8Array(PART_SIZE);
  let bufferPosition = 0;
  let partNumber = 1;

  const uploadPart = async (data: Uint8Array) => {
    const partCommand = new UploadPartCommand({
      Bucket: loc.bucketName,
      Key: loc.objectKey,
      UploadId: uploadId,
      PartNumber: partNumber,
      Body: data,
      ContentLength: data.length,
    });
    const partResponse = await S3.send(partCommand);
    partETags.push({
      PartNumber: partNumber,
      ETag: partResponse.ETag,
    });
    partNumber++;
  };

  while (true) {
    const { done, value } = await reader.read();

    if (done) {
      if (bufferPosition > 0) {
        await uploadPart(buffer.slice(0, bufferPosition));
      }
      break;
    }

    let valuePosition = 0;
    while (valuePosition < value.length) {
      const spaceLeft = PART_SIZE - bufferPosition;
      const chunk = value.slice(
        valuePosition,
        valuePosition + Math.min(value.length - valuePosition, spaceLeft),
      );
      buffer.set(chunk, bufferPosition);
      bufferPosition += chunk.length;
      valuePosition += chunk.length;

      if (bufferPosition === PART_SIZE) {
        await uploadPart(buffer);
        bufferPosition = 0;
      }
      assert(
        bufferPosition < PART_SIZE,
        "Buffer position should be less than part size",
      );
    }
  }

  const completeCommand = new CompleteMultipartUploadCommand({
    Bucket: loc.bucketName,
    Key: loc.objectKey,
    UploadId: uploadId,
    MultipartUpload: {
      Parts: partETags,
    },
  });
  const completeResponse = await S3.send(completeCommand);
  return completeResponse;
}

async function copyObjectByQuery(
  orgName: string,
  queryBody: any,
  destinationBucket: string,
) {
  const key = queryToKey(queryBody);
  return copyObject(
    { bucketName: orgName, objectKey: key },
    { bucketName: destinationBucket, objectKey: key },
  );
}

async function copyObject(source: ObjectLocation, destination: ObjectLocation) {
  const command = new CopyObjectCommand({
    CopySource: encodeURIComponent(`${source.bucketName}/${source.objectKey}`),
    Bucket: destination.bucketName,
    Key: destination.objectKey,
  });
  const response = await S3.send(command);
  return response;
}

async function createBucketWithLifecycle(bucketName: string) {
  try {
    await S3.send(new HeadBucketCommand({ Bucket: bucketName }));
    logger.log(`Bucket ${bucketName} already exists, skipping creation`);
    return;
  } catch (error) {
    if (!(error instanceof NotFound)) {
      throw error;
    }
  }

  await S3.send(new CreateBucketCommand({ Bucket: bucketName }));
  logger.log(`Created R2 bucket: ${bucketName}`);

  await S3.send(
    new PutBucketLifecycleConfigurationCommand({
      Bucket: bucketName,
      LifecycleConfiguration: {
        Rules: [
          {
            ID: "expire-after-14-days",
            Status: "Enabled",
            Expiration: { Days: 14 },
            Filter: {},
          },
        ],
      },
    }),
  );
  logger.log(`Set 14-day expiration policy on bucket: ${bucketName}`);
}

async function putBase64Image(
  bucketName: string,
  objectKey: string,
  base64Data: string,
  contentType: string = "image/png",
): Promise<void> {
  const base64Clean = base64Data.replace(/^data:[^;]+;base64,/, "");
  const buffer = Buffer.from(base64Clean, "base64");

  const command = new PutObjectCommand({
    Bucket: bucketName,
    Key: objectKey,
    Body: buffer,
    ContentType: contentType,
  });

  await S3.send(command);
}

async function objectExists(
  bucketName: string,
  objectKey: string,
): Promise<boolean> {
  try {
    await S3.send(
      new HeadObjectCommand({
        Bucket: bucketName,
        Key: objectKey,
      }),
    );
    return true;
  } catch (error) {
    if (error instanceof NotFound) {
      return false;
    }
    throw error;
  }
}

async function getPreviewSignedUrl(
  bucketName: string,
  objectKey: string,
  expirationSeconds: number = 900,
): Promise<string | null> {
  const exists = await objectExists(bucketName, objectKey);
  if (!exists) {
    return null;
  }

  const command = new GetObjectCommand({
    Bucket: bucketName,
    Key: objectKey,
  });

  return getSignedUrl(S3, command, { expiresIn: expirationSeconds });
}

async function putSignedUrl(
  bucketName: string,
  objectKey: string,
  expirationSeconds: number = 900,
): Promise<string> {
  const command = new PutObjectCommand({
    Bucket: bucketName,
    Key: objectKey,
  });

  return getSignedUrl(S3, command, { expiresIn: expirationSeconds });
}

export {
  getObjectByQuery,
  putObjectByQuery,
  copyObjectByQuery,
  createBucketWithLifecycle,
  putBase64Image,
  getPreviewSignedUrl,
  putSignedUrl,
};
