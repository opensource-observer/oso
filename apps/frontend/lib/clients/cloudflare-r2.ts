import {
  S3Client,
  GetObjectCommand,
  PutObjectCommand,
} from "@aws-sdk/client-s3";
import type { NodeJsClient } from "@smithy/types";
import { createHash } from "node:crypto";
import { Readable } from "node:stream";
import {
  CLOUDFLARE_R2_ENDPOINT,
  CLOUDFLARE_R2_ACCESS_KEY_ID,
  CLOUDFLARE_R2_SECRET_ACCESS_KEY,
} from "@/lib/config";

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
  body: Readable,
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
  body: Readable,
) {
  const command = new PutObjectCommand({
    Bucket: bucketName,
    Key: objectKey,
    Body: body,
  });
  const response = await S3.send(command);
  return response;
}

export { getObjectByQuery, putObjectByQuery };
