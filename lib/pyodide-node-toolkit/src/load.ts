"use server";
import { loadPyodide, PyodideAPI } from "pyodide";
import * as fsPromises from "fs/promises";
import { extract } from "tar";
import { logger } from "@opensource-observer/utils/logger";
import { withContext } from "@opensource-observer/utils";

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

/**
 * Given a path to a python artifact packaged with `packagePythonArtifacts`,
 * load a pyodide environment. This allows loading the environment offline.
 *
 * @param runtimeEnvironmentPath
 */
export async function loadPyodideEnvironment(
  runtimeEnvironmentPath: string,
): Promise<PyodideAPI> {
  const pyodide = await loadPyodide();

  logger.debug("Loading pyodide environment from ", runtimeEnvironmentPath);
  await withContext(new TempDirContext("pyodide-runtime-"), async (tmpDir) => {
    // Unpack the artifact to a temp directory
    await extract({
      file: runtimeEnvironmentPath,
      cwd: tmpDir,
    });

    // List all the whl files in the unpacked directory
    const files = await fsPromises.readdir(tmpDir);
    const whlFiles = files.filter((f) => f.endsWith(".whl"));

    // Load all of the wheel files using unpackArchive
    for (const whlFile of whlFiles) {
      await loadLocalWheelFileIntoPyodide(pyodide, `${tmpDir}/${whlFile}`);
    }
  });
  return pyodide;
}
