import { z } from "zod";
import { ValidationErrors } from "./errors";

export const CreateInvitationSchema = z.object({
  email: z.string().email("Invalid email address"),
  orgName: z.string().min(1, "Organization name is required"),
});

export const AcceptInvitationSchema = z.object({
  invitationId: z.string().uuid("Invalid invitation ID"),
});

export const RevokeInvitationSchema = z.object({
  invitationId: z.string().uuid("Invalid invitation ID"),
});

export const RemoveMemberSchema = z.object({
  orgName: z.string().min(1, "Organization name is required"),
  userId: z.string().uuid("Invalid user ID"),
});

export const UpdateMemberRoleSchema = z.object({
  orgName: z.string().min(1, "Organization name is required"),
  userId: z.string().uuid("Invalid user ID"),
  role: z.enum(["owner", "admin", "member"]),
});

export const AddUserByEmailSchema = z.object({
  orgName: z.string().min(1, "Organization name is required"),
  email: z.string().email("Invalid email address"),
  role: z.enum(["owner", "admin", "member"]),
});

export function validateInput<T>(schema: z.ZodSchema<T>, input: unknown): T {
  const result = schema.safeParse(input);

  if (!result.success) {
    const validationErrors = result.error.errors.map((err) => ({
      path: err.path.map(String),
      message: err.message,
    }));

    const flattened = result.error.flatten();
    const rawErrorMessage = JSON.stringify(flattened, null, 2);

    throw ValidationErrors.validationFailed(validationErrors, rawErrorMessage);
  }

  return result.data;
}
