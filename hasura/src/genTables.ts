import path from "node:path";
import fs from "node:fs/promises";
import { fileURLToPath } from "node:url";
import * as yaml from "yaml";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
// YAML file extension
const EXTENSION = ".yaml";
// Recursively scan this directory for database tables
const modelDir = path.resolve(__dirname, "../../dbt/models/marts/");
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
      columns: string;
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
        columns: "*",
        filter: {},
        allow_aggregations: false,
      },
      comment: "",
    },
  ],
});

async function main(): Promise<void> {
  console.log(`Generating tables from ${modelDir}`);
  // Recursively scan all files in the model directory
  const allFiles = await fs.readdir(modelDir, { recursive: true });
  // Get the basename as the table name
  const tableNames = allFiles
    .filter((f) => f.endsWith(".sql"))
    .map((f) => path.basename(f, ".sql"));
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
    console.warn(e);
  });
