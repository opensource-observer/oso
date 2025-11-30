"use server";
import { loadPyodide, PyodideAPI } from "pyodide";
import * as fsPromises from "fs/promises";
import { extract } from "tar";
import { logger } from "@opensource-observer/utils/logger";
import { Context, withContext } from "@opensource-observer/utils";
import * as path from "path";

import { TempDirContext } from "./utils.js";

export async function loadLocalWheelFileIntoPyodide(
  pyodide: PyodideAPI,
  wheelFilePath: string,
): Promise<void> {
  // Load file into memory
  const wheelData = await fsPromises.readFile(wheelFilePath);

  // Get uint8array from whl file data
  const wheelUint8Array = new Uint8Array(wheelData.buffer);
  pyodide.unpackArchive(wheelUint8Array, "whl");
}

class ExistingPath implements Context<string> {
  private path: string;

  constructor(path: string) {
    this.path = path;
  }
  async enter(): Promise<string> {
    return this.path;
  }

  async exit(): Promise<void> {
    return;
  }
}

type LoadPyodideOptions = {
  runtimeEnvironmentPath: string;
  unpackPath?: string;
  noExtract?: boolean;
};

export async function loadPyodideFromDirectory(
  workDir: string,
): Promise<PyodideAPI> {
  const workDirAbsPath = path.resolve(workDir);
  logger.info(`Extracting pyodide environment into ${workDirAbsPath}`);

  // Verify the contents of fake-import.js if it exists
  // This is just a test file to verify that imports work correctly
  // This is a temporary debug step
  const fakeImportPath = path.join(workDirAbsPath, "fake-import.js");
  const fakeImportStat = await fsPromises.stat(fakeImportPath);
  if (fakeImportStat.isFile()) {
    const fakeImportContents = await fsPromises.readFile(
      fakeImportPath,
      "utf-8",
    );
    logger.info(`Contents of fake-import.js: \n\n${fakeImportContents}`);

    // TEST IMPORTING THE fake-import.js FILE
    const fake = await (import(
      `file://${path.join(workDirAbsPath, "fake-import.js")}`
    ) as Promise<string>);
    logger.info(`fake-import result: ${fake}`);
  } else {
    logger.info(
      `No fake-import.js file found at ${fakeImportPath}. Skipping import test.`,
    );
  }

  // TEMP FOR DEBUGGING ONLY
  logger.info("Listing files in the pyodide environment");
  const pythonEnvFiles = await fsPromises.readdir(workDirAbsPath, {
    recursive: true,
  });
  logger.info(`pyodide-env: ${pythonEnvFiles}`);
  // For each of the files list the stats (like size, isFile, isDirectory)
  for (const file of pythonEnvFiles) {
    const stat = await fsPromises.stat(path.join(workDir, file));
    logger.info(
      `pyodide-env-file: ${file} - size: ${stat.size} - isFile: ${stat.isFile()} - isDirectory: ${stat.isDirectory()}`,
    );
  }

  const pyodide = await loadPyodide({
    indexURL: `${workDirAbsPath}/core/`,
  });

  // List all the whl files in the unpacked directory
  const files = await fsPromises.readdir(workDirAbsPath);
  const whlFiles = files.filter((f) => f.endsWith(".whl"));

  // Load all of the wheel files using unpackArchive
  for (const whlFile of whlFiles) {
    await loadLocalWheelFileIntoPyodide(
      pyodide,
      `${workDirAbsPath}/${whlFile}`,
    );
  }
  return pyodide;
}

/**
 * Given a path to a python artifact packaged with `packagePythonArtifacts`,
 * load a pyodide environment. This allows loading the environment offline.
 *
 * @param runtimeEnvironmentPath
 */
export async function loadPyodideEnvironment({
  runtimeEnvironmentPath,
  unpackPath,
  noExtract = false,
}: LoadPyodideOptions): Promise<PyodideAPI> {
  logger.debug(`Loading pyodide environment from ${runtimeEnvironmentPath}`);
  // Check that the runtimeEnvironmentPath exists on the file system
  const stat = await fsPromises.stat(runtimeEnvironmentPath);
  if (!stat.isFile()) {
    throw new Error(`${runtimeEnvironmentPath} is not a file`);
  }
  let context: Context<string> = new TempDirContext("pyodide-runtime-");
  if (unpackPath) {
    logger.info("unpacking pyodide into an already existing directory");
    context = new ExistingPath(unpackPath);
  }

  return await withContext(context, async (workDir) => {
    const workDirAbsPath = path.resolve(workDir);
    // Unpack the artifact to a temp directory
    if (!noExtract) {
      await extract({
        file: runtimeEnvironmentPath,
        cwd: workDirAbsPath,
      });
    }
    return await loadPyodideFromDirectory(workDir);
  });
}
