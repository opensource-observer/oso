import yargs from "yargs";
//import { ArgumentsCamelCase } from "yargs";
import { hideBin } from "yargs/helpers";
import { packagePythonArtifacts } from "./build.js";
import { logger } from "@opensource-observer/utils";
import * as path from "path";

// type BeforeClientArgs = ArgumentsCamelCase<{
//   "github-app-private-key": unknown;
//   "github-app-id": unknown;
//   "admin-team-name": string;
// }>;

interface PackageForNodePyodide {
  outputPath: string;
  pypiDeps: string[];
  uvProjects: string[];
}

const cli = yargs(hideBin(process.argv))
  .command<PackageForNodePyodide>(
    "package <output-path>",
    "Package python artifacts for pyodide in node",
    (yags) => {
      yags.positional("output-path", {
        type: "string",
        description: "The output-path to use",
      });
      yags.option("pypi-deps", {
        type: "array",
        description: "The pypi dependencies to include",
        default: [],
      });
      yags.option("uv-projects", {
        type: "array",
        description:
          "The uv projects to include in the format path/to/workspace:package_name",
        default: [],
      });
    },
    (args) => {
      console.log("Packaging python artifacts for pyodide in node", args);

      return packagePythonArtifacts(
        args.pypiDeps as string[],
        args.uvProjects as string[],
        path.resolve(args.outputPath),
      ).then((outputTarBallPath) => {
        console.log(`Packaged python artifacts at ${outputTarBallPath}`);
      });
    },
  )
  .demandCommand()
  .help("h")
  .alias("h", "help");

function main() {
  // This was necessary to satisfy the es-lint no-floating-promises check.
  const promise = cli.parse() as Promise<unknown>;
  promise.catch((err) => {
    logger.error("error caught running the cli", err);
  });
}

main();
