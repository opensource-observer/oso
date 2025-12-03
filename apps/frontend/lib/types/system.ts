import z from "zod";

export const systemCredentialsSchema = z.object({
  source: z.string(),
});

export type SystemCredentials = z.infer<typeof systemCredentialsSchema>;
