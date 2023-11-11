import { DateTime } from "luxon";

export function coerceDateTime(input: string) {
  const date = DateTime.fromISO(input).toUTC();
  if (!date.isValid) {
    throw new Error(`input "${input}" is not a valid date`);
  }
  return date;
}

export function coerceDateTimeOrNow(input: string) {
  if (input) {
    return coerceDateTime(input);
  }
  return DateTime.now();
}
