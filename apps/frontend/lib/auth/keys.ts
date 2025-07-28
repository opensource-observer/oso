import { generateApiKey as genKey, GenerationOptions } from "generate-api-key";
import { CustomFunctionMeta } from "@plasmicapp/loader-nextjs";

const generateApiKeyMeta: CustomFunctionMeta<typeof generateApiKey> = {
  name: "generateApiKey",
  params: [
    {
      name: "options",
      type: "object",
      description: "See https://www.npmjs.com/package/generate-api-key",
    },
  ],
  returnValue: {
    type: "string",
    description: "the API key",
  },
};

function generateApiKey(opts: GenerationOptions): string {
  const result = genKey(opts);
  if (Array.isArray(result)) {
    return result.join("");
  }
  return result;
}

export { generateApiKey, generateApiKeyMeta };
