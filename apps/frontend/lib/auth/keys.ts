import { generateApiKey as genKey, GenerationOptions } from "generate-api-key";

function generateApiKey(opts: GenerationOptions): string {
  const result = genKey(opts);
  if (Array.isArray(result)) {
    return result.join("");
  }
  return result;
}

export { generateApiKey };
