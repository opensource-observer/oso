import { z } from "zod";

export const queryMetadataSchema = z.object({
  orgName: z.string(),
  datasetName: z.string().optional(),
});

export type QueryMetadata = z.infer<typeof queryMetadataSchema>;
