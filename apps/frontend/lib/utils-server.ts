import { createHash } from "node:crypto";

export function hashObject(obj: any): string {
  const queryStr = JSON.stringify(obj);
  const normalized = queryStr.toLowerCase().trim();
  const buffer = Buffer.from(normalized, "utf-8");
  const hash = createHash("md5").update(buffer).digest("hex");
  return hash;
}
