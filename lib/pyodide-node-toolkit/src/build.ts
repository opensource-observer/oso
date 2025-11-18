import { loadPyodide, PyodideAPI } from "pyodide";
import { exec } from "child_process";
import * as fsPromises from "fs/promises";
import * as os from "os";
import * as path from "path";
import util from "util";
import { create, extract } from "tar";
import { mkdirp } from "mkdirp";
import { logger } from "@opensource-observer/utils";
import { createWriteStream } from "fs";
import { Readable } from "stream";
import type { ReadableStream } from "stream/web";

// Wrap exec in a promise
const execPromise = util.promisify(exec);

export type PyPIPackageWithMocks = {
  name: string;
  mockPackages: { name: string; version: string }[];
};

export type PyPIPackage = string | PyPIPackageWithMocks;

export type PackageForNodePyodideOptions = {
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

/**
 * Allows packaging of python artifacts for loading the environment without
 * installing anything. This should allow for fully offline loading of a
 * pyodide environment with the specified packages.
 */
export async function packagePythonArtifacts({
  pypiDeps,
  outputPath,
  uvProjects = [],
}: PackageForNodePyodideOptions): Promise<string> {
  const distPath = `${outputPath}/dist`;
  await mkdirp(distPath);

  console.log("distPath", distPath);

  const pyodide = await loadPyodide({
    // packages: [
    //   "micropip",
    //   ...pypiDependencies,
    // ],
    packageCacheDir: distPath,
  });
  await pyodide.loadPackage("micropip");

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

  await pyodide.runPythonAsync(`
    from sqlglot import parse_one

    print(repr(parse_one("SELECT * FROM test")))
  `);

  // Load uv project dependencies
  for (const dep of uvProjects) {
    // Build the wheel file for the uv project
    const [sourcePath, packageName] = dep.split(":");
    await buildLocalUvWorkspaceWheel(packageName, sourcePath, distPath);
    // Delete all tarballs that were created in the outputPath
    const files = await fsPromises.readdir(distPath);
    for (const file of files) {
      if (file.endsWith(".tar.gz")) {
        await fsPromises.unlink(`${distPath}/${file}`);
      }
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
      console.log(
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
  console.log("Packaged files:", distFiles);

  const outputTarBallPath = `${outputPath}/python_artifacts.tar.gz`;

  // Tarball all the wheel files in the outputPath
  await create(
    {
      gzip: true,
      file: outputTarBallPath,
      cwd: distPath,
    },
    distFiles,
  );

  return outputTarBallPath;
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
  const tmpDir = await fsPromises.mkdtemp(path.join(os.tmpdir(), "temp-dir-"));
  const pyodide = await loadPyodide();

  try {
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
  } finally {
    // Clean up the temporary directory
    await fsPromises.rm(tmpDir, { recursive: true, force: true });
  }
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
