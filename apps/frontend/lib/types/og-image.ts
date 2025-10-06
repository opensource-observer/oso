import { z } from "zod";

export const ogImageInfoSchema = z.object({
  orgName: z.string(),
  notebookName: z.string(),
  authorAvatar: z.string().nullable(),
  description: z.string().nullable(),
});

export type OGImageInfo = z.infer<typeof ogImageInfoSchema>;
