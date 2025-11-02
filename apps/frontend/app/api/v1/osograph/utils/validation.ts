import { z } from "zod";
import { ValidationErrors } from "@/app/api/v1/osograph/utils/errors";

const MAX_PREVIEW_SIZE_MB = 1 * 1024 * 1024;
const PNG_HEADER = Buffer.from([
  0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a,
]); // PNG magic bytes

export function validateBase64PngImage(base64Data: string): void {
  if (!base64Data.startsWith("data:image/png;base64,")) {
    throw new Error("Invalid image format. Expected PNG data URL.");
  }

  const base64Content = base64Data.replace(/^data:[^;]+;base64,/, "");

  if (base64Content.length > (MAX_PREVIEW_SIZE_MB * 4) / 3) {
    throw new Error("Image is too large.");
  }

  try {
    const buffer = Buffer.from(base64Content, "base64");

    if (!buffer.subarray(0, 8).equals(PNG_HEADER)) {
      throw new Error("Invalid PNG header.");
    }

    if (buffer.length > MAX_PREVIEW_SIZE_MB) {
      throw new Error("Image is too large.");
    }
  } catch (error) {
    if (error instanceof Error && error.message.includes("Invalid PNG")) {
      throw error;
    }
    throw new Error("Invalid base64 encoding or corrupted image data.");
  }
}

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
