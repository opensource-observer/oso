import {
  S3Client,
  GetObjectCommand,
  CreateMultipartUploadCommand,
  CompleteMultipartUploadCommand,
  UploadPartCommand,
  CompletedPart,
} from "@aws-sdk/client-s3";
import type { NodeJsClient } from "@smithy/types";
import { createHash } from "node:crypto";
import {
  CLOUDFLARE_R2_ENDPOINT,
  CLOUDFLARE_R2_ACCESS_KEY_ID,
  CLOUDFLARE_R2_SECRET_ACCESS_KEY,
} from "@/lib/config";
import { assert } from "@opensource-observer/utils";

const PART_SIZE = 10 * 1024 * 1024; // 10MB

const S3 = new S3Client({
  region: "auto",
  endpoint: CLOUDFLARE_R2_ENDPOINT,
  credentials: {
    accessKeyId: CLOUDFLARE_R2_ACCESS_KEY_ID,
    secretAccessKey: CLOUDFLARE_R2_SECRET_ACCESS_KEY,
  },
}) as NodeJsClient<S3Client>;

function queryToKey(queryBody: any): string {
  const queryStr = JSON.stringify(queryBody);
  const normalized = queryStr.toLowerCase().trim();
  const buffer = Buffer.from(normalized, "utf-8");
  const hash = createHash("md5").update(buffer).digest("hex");
  return hash;
}

async function getObjectByQuery(orgName: string, queryBody: any) {
  const key = queryToKey(queryBody);
  return getObject(orgName, key);
}

async function putObjectByQuery(
  orgName: string,
  queryBody: any,
  body: ReadableStream,
) {
  const key = queryToKey(queryBody);
  return putObject(orgName, key, body);
}

async function getObject(bucketName: string, objectKey: string) {
  const command = new GetObjectCommand({
    Bucket: bucketName,
    Key: objectKey,
  });
  const response = await S3.send(command);
  return response;
}

async function putObject(
  bucketName: string,
  objectKey: string,
  body: ReadableStream,
) {
  // https://developers.cloudflare.com/r2/objects/multipart-objects/
  // Part sizes must be at least 5 MB in size, except for the last part.
  // Part sizes must be less than 5 GB
  // Part sizes must be the same size except for the last part
  const createCommand = new CreateMultipartUploadCommand({
    Bucket: bucketName,
    Key: objectKey,
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
      Bucket: bucketName,
      Key: objectKey,
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

  // eslint-disable-next-line no-constant-condition
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
    Bucket: bucketName,
    Key: objectKey,
    UploadId: uploadId,
    MultipartUpload: {
      Parts: partETags,
    },
  });
  const completeResponse = await S3.send(completeCommand);
  return completeResponse;
}

export { getObjectByQuery, putObjectByQuery };
