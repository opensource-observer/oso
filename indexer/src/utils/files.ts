import * as fs from "fs/promises";

export async function fileExists(filePath: string): Promise<boolean> {
  try {
    // Use fs.promises.access() with the fs.constants.F_OK flag to check if the file exists
    await fs.access(filePath, fs.constants.F_OK);
    return true;
  } catch (error) {
    // If an error is thrown, the file does not exist
    return false;
  }
}
