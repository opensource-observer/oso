import { z } from "zod";

export const queryMetadataSchema = z.object({
  user: z.string(),
  timestamp: z.string(),
  orgName: z.string(),
  orgId: z.string(),
  datasetName: z.string().optional(),
});

export type QueryMetadata = z.infer<typeof queryMetadataSchema>;
