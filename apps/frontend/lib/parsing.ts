import dayjs from "dayjs";
import _ from "lodash";
import type { EntityData } from "./types/db";

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

/**
 * Given an id, try to find the id in EntityData[] and return the name
 * Note: the `==` is intentional here, since we may be comparing a string to a number
 */
const entityIdToLabel = (id: number | string, entityData?: EntityData[]) =>
  entityData?.find((x) => x.id == id)?.name ?? id;

export {
  csvToArray,
  stringToIntArray,
  eventTimeToLabel,
  eventTypeToLabel,
  entityIdToLabel,
};
