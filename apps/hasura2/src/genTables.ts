import path from "node:path";
import fs from "node:fs/promises";
import { fileURLToPath } from "node:url";
import * as yaml from "yaml";
import { exec } from "node:child_process";
import * as util from "util";

const execPromise = util.promisify(exec);

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
// YAML file extension
const EXTENSION = ".yaml";
// Where to store all table configs
const tablesDir = path.resolve(
  __dirname,
  "../metadata/databases/cloudsql/tables/",
);
// Should map to the tables field in ./metadata/databases/databases.yaml
const tablesListAbsPath = path.format({
  dir: tablesDir,
  name: "tables",
  ext: EXTENSION,
});

// Schema for Hasura table configuration
type TableConfig = {
  table: {
    name: string;
    schema: string;
  };
  select_permissions: {
    role: string;
    permission: {
      columns: string | string[];
      filter: Record<string, unknown>;
      allow_aggregations: boolean;
    };
    comment: string;
  }[];
};

// Create a table configuration object
const createConfig = (name: string): TableConfig => ({
  table: {
    name: name,
    schema: "public",
  },
  select_permissions: [
    {
      role: "anonymous",
      permission: {
        // Anonymous cannot see any columns
        columns: "*",
        filter: {},
        allow_aggregations: false,
      },
      comment: "",
    },
    {
      role: "user",
      permission: {
        columns: "*",
        filter: {},
        allow_aggregations: false,
      },
      comment: "",
    },
    {
      role: "developer",
      permission: {
        columns: "*",
        filter: {},
        allow_aggregations: true,
      },
      comment: "",
    },
  ],
});

type ModelConfig = {
  name: string;
  config: {
    meta: {
      sync_to_db: boolean;
    };
  };
};

async function main(): Promise<void> {
  const target = process.env.DBT_TARGET;
  if (!target) {
    throw new Error("specify a DBT_TARGET");
  }
  console.log(`Generating tables from dbt`);

  // FIXME... this isn't very portable
  // Run dbt to get the json
  const repoRoot = path.resolve("../../");
  const modelsList = await execPromise(
    `${repoRoot}/.venv/bin/dbt ls -q --output json --select marts.* --target ${target} --resource-type model`,
    {
      cwd: repoRoot,
    },
  );

  const modelsConfigRaw = modelsList.stdout.split("\n");
  const modelConfigs: ModelConfig[] = [];
  for (const raw of modelsConfigRaw) {
    const trimmed = raw.trim();
    if (trimmed === "") {
      continue;
    }
    const modelConfig = JSON.parse(trimmed) as {
      name: string;
      config: {
        meta: {
          sync_to_db: boolean;
        };
      };
    };
    modelConfigs.push(modelConfig);
  }
  const filteredConfigs = modelConfigs.filter((c) => {
    return c.config.meta.sync_to_db === true;
  });

  const tableNames = filteredConfigs.map((c) => {
    return c.name;
  });

  // Recursively scan all files in the model directory
  //const allFiles = await fs.readdir(modelDir, { recursive: true });
  // Get the basename as the table name
  // const tableNames = allFiles
  //   .filter((f) => f.endsWith(".sql"))
  //   .map((f) => path.basename(f, ".sql"));
  console.log("Tables:");
  console.log(tableNames);
  // Write the list of tables
  await fs.writeFile(
    tablesListAbsPath,
    yaml.stringify(
      tableNames.map(
        (n) => `!include ${path.format({ name: n, ext: EXTENSION })}`,
      ),
    ),
  );
  // Write a table config for each table
  await Promise.all(
    tableNames.map(async (n) => {
      const config = createConfig(n);
      const absPath = path.format({
        dir: tablesDir,
        name: n,
        ext: EXTENSION,
      });
      await fs.writeFile(absPath, yaml.stringify(config));
    }),
  );
}

main()
  .then(() => console.log("Done"))
  .catch((e) => {
    //console.warn(e);
    throw e;
  });
