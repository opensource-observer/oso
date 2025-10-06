import { z } from "zod";

export const resourcePermissionResponseSchema = z.object({
  hasAccess: z.boolean(),
  permissionLevel: z
    .enum(["read", "write", "admin", "owner"])
    .nullable()
    .transform((val) => val ?? "none")
    .pipe(z.enum(["none", "read", "write", "admin", "owner"])),
  resourceId: z.string(),
});

export type ResourcePermissionResponse = z.infer<
  typeof resourcePermissionResponseSchema
>;
