import dayjs from "dayjs";
import _ from "lodash";

/**
 * Parse a comma-separated list into a string array
 * @param csv
 * @returns
 */
const csvToArray = (csv?: string | null) =>
  csv?.split(",").map((x) => x.trim()) ?? [];

/**
 * Parses string IDs into integers
 * @param ids
 * @returns
 */
const stringToIntArray = (ids?: string[]): number[] =>
  ids?.map((id) => parseInt(id)).filter((id) => !!id && !isNaN(id)) ?? [];

/**
 * Convert the event time to a date label
 */
const eventTimeToLabel = (t: any) => dayjs(t).format("YYYY-MM-DD");

/**
 * If we get enums (e.g. NPM_PACKAGE), normalize it into a readable label
 * @param t
 * @returns
 */
const eventTypeToLabel = (t: string) => _.capitalize(t.replace(/_/g, " "));

export { csvToArray, stringToIntArray, eventTimeToLabel, eventTypeToLabel };
