import { loadPyodide } from "pyodide";
import { exec } from "child_process";
import * as fsPromises from "fs/promises";
import util from "util";
import { create } from "tar";
import { mkdirp } from "mkdirp";
import { logger } from "@opensource-observer/utils";

// Wrap exec in a promise
const execPromise = util.promisify(exec);

export type PyPIPackageWithMocks = {
  name: string;
  mockPackages: { name: string; version: string }[];
};

export type PyPIPackage = string | PyPIPackageWithMocks;

export type PackageForNodePyodideOptions = {
  outputPath: string;
  pypiDeps: string[];
  uvProjects: string[];
};

/**
 * Allows packaging of python artifacts for loading the environment without
 * installing anything.
 */
export async function packagePythonArtifacts(
  pypiDependencies: PyPIPackage[],
  uvProjects: string[],
  outputPath: string,
): Promise<string> {
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

  const pypiDependenciesWithMocks = pypiDependencies.filter(
    (dep) => typeof dep !== "string",
  ) as PyPIPackageWithMocks[];
  const pypiDependenciesWithoutMocks = pypiDependencies.filter(
    (dep) => typeof dep === "string",
  ) as string[];

  // Install packages with mocks first. This is added to allow the installation
  // of some python libraries that need to be tricked into installing correctly.
  // YMMV and this will not guarantee that the library works, simply that it
  // installs without error. In some use cases this is what we want because the
  // specific functionality required doesn't use the mocked parts or pyodide
  // provides a different version that _might_ work but the dependency might try
  // to require a version that doesn't exist for pyodide.
  for (const pkg of pypiDependenciesWithMocks) {
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
    packages: pypiDependenciesWithoutMocks,
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
    // const files = await fsPromises.readdir(outputPath);
    // for (const file of files) {
    //   if (file.endsWith(".tar.gz")) {
    //     await fsPromises.unlink(`${outputPath}/${file}`);
    //   }
    // }
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

/**
 * Given a path to a python artifact packaged with `packagePythonArtifacts`,
 * load a pyodide environment. This allows loading the environment without
 * any downloading at runtime.
 *
 * @param artifactPath
 */
export async function loadPyodideEnvironment(
  _artifactPath: string,
): Promise<any> {}

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
