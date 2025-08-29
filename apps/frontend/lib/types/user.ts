import { z } from "zod";

// Zod schemas
export const UserRoleSchema = z.enum(["anonymous", "user", "admin"]);
export const OrgRoleSchema = z.enum(["admin", "member"]);

export const BaseUserSchema = z.object({
  role: UserRoleSchema,
  host: z.string().nullable(),
});

export const AnonUserSchema = BaseUserSchema.extend({
  role: z.literal("anonymous"),
});

export const UserDetailsSchema = z.object({
  userId: z.string(),
  keyName: z.string(),
  email: z.string().optional(),
  name: z.string(),
});

export const OrganizationDetailsSchema = z.object({
  orgId: z.string(),
  orgName: z.string(),
  orgRole: OrgRoleSchema,
});

export const NormalUserSchema = BaseUserSchema.extend({
  role: z.literal("user"),
})
  .merge(UserDetailsSchema)
  .merge(OrganizationDetailsSchema);

export const AdminUserSchema = BaseUserSchema.extend({
  role: z.literal("admin"),
})
  .merge(UserDetailsSchema)
  .merge(OrganizationDetailsSchema);

export const AuthUserSchema = z.union([NormalUserSchema, AdminUserSchema]);
export const UserSchema = z.union([AnonUserSchema, AuthUserSchema]);

// Exported types inferred from Zod schemas
export type UserRole = z.infer<typeof UserRoleSchema>;
export type OrgRole = z.infer<typeof OrgRoleSchema>;
export type BaseUser = z.infer<typeof BaseUserSchema>;
export type AnonUser = z.infer<typeof AnonUserSchema>;
export type UserDetails = z.infer<typeof UserDetailsSchema>;
export type OrganizationDetails = z.infer<typeof OrganizationDetailsSchema>;
export type NormalUser = z.infer<typeof NormalUserSchema>;
export type AdminUser = z.infer<typeof AdminUserSchema>;
export type AuthUser = z.infer<typeof AuthUserSchema>;
export type User = z.infer<typeof UserSchema>;
