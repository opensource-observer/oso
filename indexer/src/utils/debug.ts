import { DateTime } from "luxon";
import { logger } from "./logger.js";

class Timer {
  private start: DateTime;

  constructor() {
    this.start = DateTime.now();
  }

  finish(message: string) {
    logger.info(`${this.start.diffNow().milliseconds * -1}ms: ${message}`);
  }
}

export function timer(label: string) {
  const timer = new Timer();
  return () => {
    timer.finish(`${label} completed`);
  };
}
