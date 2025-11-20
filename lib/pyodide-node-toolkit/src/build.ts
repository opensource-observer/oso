import { loadPyodide, PyodideAPI } from "pyodide";
import { exec } from "child_process";
import * as fsPromises from "fs/promises";
import * as path from "path";
import util from "util";
import { create, extract } from "tar";
import { mkdirp } from "mkdirp";
import { logger } from "@opensource-observer/utils/src/logger";
import { createWriteStream } from "fs";
import { Readable } from "stream";
import type { ReadableStream } from "stream/web";
import { withContext } from "@opensource-observer/utils";
import { parse, TomlTable } from "smol-toml";

import { TempDirContext } from "@/utils";

// Wrap exec in a promise
const execPromise = util.promisify(exec);

export type PyPIPackageWithMocks = {
  name: string;
  mockPackages: { name: string; version: string }[];
};

export type PyPIPackage = string | PyPIPackageWithMocks;

export type PackageForNodePyodideOptions = {
  buildDirPath: string;
  outputPath: string;
  pypiDeps: PyPIPackage[];
  uvProjects?: string[];
};

/**
 * Streams a URL to a file.
 *
 * @param url The URL to download.
 * @param outputPath The local file path to save the downloaded content.
 */
async function downloadUrlToFile(url: string, outputPath: string) {
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`Failed to download ${url}: ${response.statusText}`);
  }

  const fileStream = createWriteStream(outputPath);
  const responseBody = response.body;
  if (!responseBody) {
    throw new Error(`Response body is null for ${url}`);
  }
  const readableStream = Readable.fromWeb(
    responseBody as ReadableStream<Uint8Array>,
  );
  await new Promise((resolve, reject) => {
    readableStream.pipe(fileStream);
    fileStream.on("finish", resolve);
    fileStream.on("error", reject);
  });
}

async function loadPyprojectTomlFromTarball(
  tarballPath: string,
): Promise<TomlTable> {
  return withContext(new TempDirContext(), async (tmpDir) => {
    // Extract the tarball to the temp directory
    await extract({
      file: tarballPath,
      cwd: tmpDir,
    });

    // Assume the pyproject.toml is in `<filename>/pyproject.toml`
    const files = await fsPromises.readdir(tmpDir);
    if (files.length === 0) {
      throw new Error(`No files found in tarball ${tarballPath}`);
    }
    const firstDir = files[0];
    const pyprojectPath = path.join(tmpDir, firstDir, "pyproject.toml");
    const pyprojectRaw = await fsPromises.readFile(pyprojectPath, {
      encoding: "utf-8",
    });
    return parse(pyprojectRaw);
  });
}

/**
 * Allows packaging of python artifacts for loading the environment without
 * installing anything. This should allow for fully offline loading of a
 * pyodide environment with the specified packages.
 */
export async function packagePythonArtifacts({
  pypiDeps,
  buildDirPath,
  outputPath,
  uvProjects = [],
}: PackageForNodePyodideOptions): Promise<string> {
  const distPath = `${buildDirPath}/dist`;
  await mkdirp(distPath);

  const pyodide = await loadPyodide({
    packages: ["micropip"],
    packageCacheDir: distPath,
  });

  const pypiDepsWithMocks = pypiDeps.filter(
    (dep) => typeof dep !== "string",
  ) as PyPIPackageWithMocks[];
  const pypiDepsWithoutMocks = pypiDeps.filter(
    (dep) => typeof dep === "string",
  ) as string[];

  // Install packages with mocks first. This is added to allow the installation
  // of some python libraries that need to be tricked into installing correctly.
  // YMMV and this will not guarantee that the library works, simply that it
  // installs without error. In some use cases this is what we want because the
  // specific functionality required doesn't use the mocked parts or pyodide
  // provides a different version that _might_ work but the dependency might try
  // to require a version that doesn't exist for pyodide.
  for (const pkg of pypiDepsWithMocks) {
    const micropipInstallLocals = pyodide.toPy({
      packageName: pkg.name,
      mockPackages: pkg.mockPackages,
    });
    await pyodide.runPythonAsync(
      `
      import micropip
      for mock in mockPackages:
          print(f"Adding mock package {mock['name']}=={mock['version']}")
          micropip.add_mock_package(mock['name'], mock['version'])
      print(f"Installing {packageName} with mocks")
      try:
          await micropip.install(packageName)
          print(f"done installing {packageName} with mocks")
      finally:
          for mock in mockPackages:
              print(f"Removing mock package {mock['name']}")
              micropip.remove_mock_package(mock['name'])
    `,
      { locals: micropipInstallLocals },
    );
  }

  // Install PyPI dependencies without any mocks
  const micropipInstallLocals = pyodide.toPy({
    packages: pypiDepsWithoutMocks,
  });
  await pyodide.runPythonAsync(
    `
    import micropip
    for pkg in packages:
        print(f"Installing {pkg}")
        await micropip.install(pkg)
        print(f"done installing {pkg}")
    micropip.freeze()
  `,
    { locals: micropipInstallLocals },
  );

  for (const dep of uvProjects) {
    // Build the wheel file for the uv project
    const [sourcePath, packageName] = dep.split(":");
    await buildLocalUvWorkspaceWheel(packageName, sourcePath, distPath);

    const expectedTarballPrefix = `${packageName.replace("-", "_")}-`;
    // Find the tarball that was created
    const distFiles = await fsPromises.readdir(distPath);
    const matchingTarballs = distFiles.filter(
      (f) => f.startsWith(expectedTarballPrefix) && f.endsWith(".tar.gz"),
    );
    if (matchingTarballs.length === 0) {
      throw new Error(`No tarball found for UV package ${packageName}`);
    }
    const tarballPath = `${distPath}/${matchingTarballs[0]}`;

    // Load the pyproject.toml from the tarball to find the wheel file name
    const pyproject = await loadPyprojectTomlFromTarball(tarballPath);
    const pyprojectProjectSection = pyproject.project as TomlTable;
    if (!pyprojectProjectSection) {
      throw new Error(`Invalid pyproject.toml format: missing 'project' key`);
    }
    const dependencies = (pyprojectProjectSection.dependencies ||
      []) as string[];

    const uvDeps = pyodide.toPy({
      packages: dependencies,
    });
    await pyodide.runPythonAsync(
      `
      import micropip
      for pkg in packages:
          print(f"Installing {pkg}")
          await micropip.install(pkg)
      micropip.freeze()
    `,
      { locals: uvDeps },
    );
  }
  // Delete any other tarballs that may have been created in the outputPath
  const files = await fsPromises.readdir(distPath);
  for (const file of files) {
    if (file.endsWith(".tar.gz")) {
      await fsPromises.unlink(`${distPath}/${file}`);
    }
  }

  // Load the lock file
  const lockFileContent = await pyodide.runPythonAsync(`
      import micropip
      micropip.freeze()
  `);
  // If there are _any_ packages in the lock file that reference using http/https
  // Download those packages and rehost them in the distPath

  const lockFile = JSON.parse(lockFileContent);
  if (!lockFile.packages) {
    throw new Error("Invalid lock file format: missing 'packages' key");
  }
  for (const [packageName, packageInfo] of Object.entries(lockFile.packages)) {
    const fileName: string = (packageInfo as any).file_name;
    if (fileName.startsWith("http://") || fileName.startsWith("https://")) {
      logger.debug(
        `Rehosting package ${packageName} from ${fileName} into local dist`,
      );
      // Download the file
      const url = new URL(fileName);
      const pathname = url.pathname;
      const localFileName = pathname.substring(pathname.lastIndexOf("/") + 1);
      const localFilePath = `${distPath}/${localFileName}`;
      await downloadUrlToFile(fileName, localFilePath);
    }
  }

  // List all wheel files in the distPath
  const distFiles = await fsPromises.readdir(distPath);
  logger.debug("Packaged files:", distFiles);

  const outputTarBallPath = `${buildDirPath}/python_artifacts.tar.gz`;

  // Tarball all the wheel files in the outputPath
  await create(
    {
      gzip: true,
      file: outputTarBallPath,
      cwd: distPath,
    },
    distFiles,
  );

  const absOutputPath = path.resolve(outputPath);

  await fsPromises.rename(outputTarBallPath, absOutputPath);

  return absOutputPath;
}

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

/**
 * Given a uv project that is accessible on the local filesystem, this builds a
 * python egg that can be used in a pyodide environment. This probably does not
 * work with projects that have native dependencies at this time.
 */
export async function buildLocalUvWorkspaceWheel(
  packageName: string,
  sourcePath: string,
  outputPath: string,
): Promise<void> {
  // Execute `uv build` in the sourcePath that outputs to outputPath
  try {
    await execPromise(`uv build --package ${packageName} -o ${outputPath}`, {
      cwd: sourcePath,
    });
  } catch (error) {
    logger.error(`Error building UV package: ${error}`);
    throw error;
  }
}
