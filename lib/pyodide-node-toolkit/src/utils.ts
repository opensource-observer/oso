import { type Context } from "@opensource-observer/utils";
import * as os from "os";
import * as path from "path";
import * as fsPromises from "fs/promises";

/**
 * Temporary Directory Context Manager
 */
export class TempDirContext implements Context<string> {
  private tempDirPath: string | null = null;
  private prefix: string;

  constructor(prefix?: string) {
    this.prefix = prefix ?? "temp-dir-";
  }

  async enter(): Promise<string> {
    const tempDirPrefix = path.join(os.tmpdir(), this.prefix);
    this.tempDirPath = await fsPromises.mkdtemp(tempDirPrefix);
    return this.tempDirPath;
  }

  async exit(): Promise<void> {
    if (this.tempDirPath) {
      await fsPromises.rm(this.tempDirPath, { recursive: true, force: true });
      this.tempDirPath = null;
    }
  }
}
