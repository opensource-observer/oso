import _ from "lodash";
import * as path from "path";
import { fileURLToPath } from "node:url";
import { logger } from "../utils/logger.js";
import { renderMustacheFromFile } from "./templating.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
function relativeDir(...args: string[]) {
  return path.join(__dirname, ...args);
}
const OVERVIEW_KEY = "overview";
const TEMPLATE_FILE = relativeDir("messages", "validation-message.md");
/**
 * Struct to store validation results for a single artifact
 */
type ValidationResultsItem = {
  name: string;
  messages: string[];
  errors: string[];
  warnings: string[];
  successes: string[];
};

const initValidationResultsItem = (name: string) => ({
  name,
  messages: [],
  errors: [],
  warnings: [],
  successes: [],
});

class ValidationResults {
  private overview: ValidationResultsItem;
  private results: Record<string, ValidationResultsItem>;

  static async create() {
    const vr = new ValidationResults();
    return vr;
  }

  private constructor() {
    this.overview = initValidationResultsItem("Overview");
    this.results = {};
  }

  // Add a name to the results
  private getItem(key?: string): ValidationResultsItem {
    if (!key || key === OVERVIEW_KEY) {
      return this.overview;
    }
    const item = this.results[key];
    if (!item) {
      this.results[key] = initValidationResultsItem(key);
    }
    return this.results[key];
  }

  addMessage(message: string, key?: string, ctx?: any) {
    const item = this.getItem(key);
    logger.debug({ message, ...ctx });
    item.messages.push(message);
  }

  addError(message: string, key?: string, ctx?: any) {
    const item = this.getItem(key);
    logger.warn({ message, ...ctx });
    item.errors.push(message);
  }

  addWarning(message: string, key?: string, ctx?: any) {
    const item = this.getItem(key);
    logger.warn({ message, ...ctx });
    item.warnings.push(message);
  }

  addSuccess(message: string, key?: string, ctx?: any) {
    const item = this.getItem(key);
    logger.debug({ message, ...ctx });
    item.successes.push(message);
  }

  // Render the results into the markdown file
  async render(commit_sha: string) {
    const items: ValidationResultsItem[] = [
      this.overview,
      ..._.values(this.results),
    ];

    const numErrors = _.sumBy(
      items,
      (item: ValidationResultsItem) => item.errors.length,
    );
    const numWarningsMessages = _.sumBy(
      items,
      (item: ValidationResultsItem) =>
        item.warnings.length + item.messages.length,
    );
    const summaryMessage =
      numErrors > 0
        ? `⛔ Found ${numErrors} errors ⛔`
        : numWarningsMessages > 0
          ? "⚠️ Please review messages before approving ⚠️"
          : "✅ Good to go as long as status checks pass";
    const commentBody = await renderMustacheFromFile(TEMPLATE_FILE, {
      sha: commit_sha,
      summaryMessage,
      validationItems: items,
    });

    return {
      numErrors,
      summaryMessage,
      commentBody,
    };
  }
}

export { ValidationResults };
