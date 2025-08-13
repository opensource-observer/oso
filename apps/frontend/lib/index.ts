import { NextJsPlasmicComponentLoader } from "@plasmicapp/loader-nextjs";
import { format } from "sql-formatter";
import { generateApiKey, generateApiKeyMeta } from "@/lib/auth/keys";

export function registerAllFunctions(PLASMIC: NextJsPlasmicComponentLoader) {
  // Functions
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

  PLASMIC.registerFunction(generateApiKey, generateApiKeyMeta);
}
