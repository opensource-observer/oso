import yargs from "yargs";
import { hideBin } from "yargs/helpers";
import { logger } from "@opensource-observer/utils/logger";
import * as path from "path";
import * as fsPromises from "fs/promises";
import { withContext } from "@opensource-observer/utils";

import { TempDirContext } from "@/utils.ts";
import { packagePythonArtifacts, loadPyodideEnvironment } from "@/build.ts";

interface PackageForNodePyodide {
  outputPath: string;
  pypiDeps: string[];
  uvProjects: string[];
}

interface RunPython {
  runtimeArchive: string;
  pythonFile: string;
}

const cli = yargs(hideBin(process.argv))
  .command<PackageForNodePyodide>(
    "package <output-path>",
    "Package python artifacts for pyodide in node",
    (yags) => {
      yags.option("output-path", {
        type: "string",
        description:
          "The destination path for the generated pyodide environment tarball",
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
      console.log("Packaging python artifacts for pyodide in node");

      const absOutputPath = path.resolve(args.outputPath);
      return withContext(
        new TempDirContext("pyodide-package-"),
        async (tempDir) => {
          await packagePythonArtifacts({
            buildDirPath: tempDir,
            pypiDeps: args.pypiDeps,
            uvProjects: args.uvProjects,
            outputPath: absOutputPath,
          });
          console.log(`Packaged python artifacts at ${absOutputPath}`);
        },
      );
    },
  )
  .command<RunPython>(
    "run <runtime-archive> <python-file>",
    "Run python code in pyodide in node",
    (yags) => {
      yags.positional("runtime-archive", {
        type: "string",
        description: "The runtime archive to use",
      });
      yags.positional("python-file", {
        type: "string",
        description: "The python code to run",
      });
    },
    async (args) => {
      return loadPyodideEnvironment(path.resolve(args.runtimeArchive)).then(
        async (pyodide) => {
          console.log("Running python code in pyodide in node");

          const code = await fsPromises.readFile(
            path.resolve(args.pythonFile),
            {
              encoding: "utf-8",
            },
          );

          return await pyodide.runPythonAsync(code);
        },
      );
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
