import { createHash } from "crypto";

export function generateSourceIdFromArray(a: string[]) {
  return hashFromArray(a, "sha1");
}

export function hashFromArray(a: string[], algo = "sha256") {
  const hash = createHash(algo);
  a.forEach((key) => {
    hash.update(key);
  });
  return hash.digest("hex");
}
