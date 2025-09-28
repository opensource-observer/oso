import { NextJsPlasmicComponentLoader } from "@plasmicapp/loader-nextjs";
import { format } from "sql-formatter";
import {
  compressToEncodedURIComponent,
  decompressFromEncodedURIComponent,
} from "lz-string";
import { generateApiKey, generateApiKeyMeta } from "@/lib/auth/keys";

export function registerAllFunctions(PLASMIC: NextJsPlasmicComponentLoader) {
  // sql-formatter
  PLASMIC.registerFunction(format, {
    name: "formatSql",
    params: [
      {
        name: "query",
        type: "string",
        description: "the SQL query to format",
      },
      {
        name: "options",
        type: "object",
        description: "options to pass to sql-formatter",
      },
    ],
    returnValue: {
      type: "string",
      description: "the formatted SQL",
    },
    importPath: "sql-formatter",
  });

  // lz-string
  PLASMIC.registerFunction(compressToEncodedURIComponent, {
    name: "compressToEncodedURIComponent",
    params: [
      {
        name: "input",
        type: "string",
        description: "the input string to compress",
      },
    ],
    returnValue: {
      type: "string",
      description: "the compressed string",
    },
    importPath: "lz-string",
  });

  PLASMIC.registerFunction(decompressFromEncodedURIComponent, {
    name: "decompressFromEncodedURIComponent",
    params: [
      {
        name: "compressed",
        type: "string",
        description: "the compressed string to decompress",
      },
    ],
    returnValue: {
      type: "string",
      description: "the decompressed string",
    },
    importPath: "lz-string",
  });

  // generate API keys
  PLASMIC.registerFunction(generateApiKey, generateApiKeyMeta);
}
