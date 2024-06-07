import * as fsPromise from "fs/promises";
import mustache from "mustache";

async function renderMustacheFromFile(
  filePath: string,
  params?: Record<string, unknown>,
) {
  const raw = await fsPromise.readFile(filePath, "utf-8");
  return mustache.render(raw, params);
}

export { renderMustacheFromFile };
