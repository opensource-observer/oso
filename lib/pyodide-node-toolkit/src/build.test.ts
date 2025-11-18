import 'module-alias/register';
import * as path from 'path';
import { TempDirContext } from "@/utils.ts";
import { packagePythonArtifacts, loadPyodideEnvironment } from "@/build.ts";

const CURRENT_DIR = path.resolve('/Users/raven/development/opensource-observer/oso/lib/pyodide-node-toolkit/src');
const SAMPLE_UV_WORKSPACE_DIR = path.resolve(CURRENT_DIR, '../sample_uv_workspace');


describe('build and run python packages', () => {
  let tempDirContext: TempDirContext;
  let tempDir: string; 
  beforeEach(async () => {
    tempDirContext = new TempDirContext();
    tempDir = await tempDirContext.enter();
  });

  afterEach(async () => {
    tempDirContext.exit();
    tempDir = "";
  });

  it('should build and run the python environment', async () => {
    const outputPath = path.resolve(tempDir, "env.tar.gz")
    await packagePythonArtifacts({ 
      pypiDeps: [],
      buildDirPath: tempDir,
      outputPath: outputPath,
    });

    // Load the `env.tar.gz` file and try to run the expected python function
    const pyodideEnv = await loadPyodideEnvironment(outputPath)

    const result = await pyodideEnv.runPythonAsync(`
        from sampleproject import sample_func

        sample_func()
    `);

    expect(result).toBe("SELECT");
  })
});
