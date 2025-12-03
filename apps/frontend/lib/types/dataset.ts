export const DATASET_TYPES = [
  "USER_MODEL",
  "DATA_CONNECTOR",
  "DATA_INGESTION",
] as const;

export type DatasetType = (typeof DATASET_TYPES)[number];
