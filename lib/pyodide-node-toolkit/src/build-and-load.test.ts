import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as path from "path";
import { fileURLToPath } from "url";
import { TempDirContext } from "./utils.ts";
import { packagePythonArtifacts } from "./build.ts";
import { loadPyodideEnvironment } from "./load.ts";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const CURRENT_DIR = path.resolve(__dirname);
const SAMPLE_UV_WORKSPACE_DIR = path.resolve(
  CURRENT_DIR,
  "../sample_uv_workspace",
);

describe("build and run python packages", () => {
  let tempDirContext: TempDirContext;
  let tempDir: string;
  beforeEach(async () => {
    tempDirContext = new TempDirContext();
    tempDir = await tempDirContext.enter();
  });

  afterEach(async () => {
    await tempDirContext.exit();
    tempDir = "";
  });

  it(
    "should build and run the python environment",
    { timeout: 30000 },
    async () => {
      const outputPath = path.resolve(tempDir, "env.tar.gz");
      console.log(SAMPLE_UV_WORKSPACE_DIR);
      await packagePythonArtifacts({
        pypiDeps: [],
        buildDirPath: tempDir,
        uvProjects: [`${SAMPLE_UV_WORKSPACE_DIR}:sample-project`],
        outputPath: outputPath,
      });

      // Load the `env.tar.gz` file and try to run the expected python function
      const pyodideEnv = await loadPyodideEnvironment(outputPath);

      const result = await pyodideEnv.runPythonAsync(`
        from sampleproject import sample_func

        result = sample_func()
        print(result)
        result
    `);

      expect(result).toBe("success");
    },
  );
});
