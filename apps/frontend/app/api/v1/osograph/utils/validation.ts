import { z } from "zod";
import { ValidationErrors } from "@/app/api/v1/osograph/utils/errors";

const MAX_PREVIEW_SIZE_MB = 1 * 1024 * 1024;
const PNG_HEADER = Buffer.from([
  0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a,
]); // PNG magic bytes

export function validateBase64PngImage(base64Data: string): void {
  if (!base64Data.startsWith("data:image/png;base64,")) {
    throw ValidationErrors.invalidInput(
      "preview",
      "Invalid image format. Expected PNG data URL.",
    );
  }

  const base64Content = base64Data.replace(/^data:[^;]+;base64,/, "");

  if (base64Content.length > (MAX_PREVIEW_SIZE_MB * 4) / 3) {
    throw ValidationErrors.invalidInput(
      "preview",
      "Image is too large. Maximum size is 1MB.",
    );
  }

  try {
    const buffer = Buffer.from(base64Content, "base64");

    if (!buffer.subarray(0, 8).equals(PNG_HEADER)) {
      throw ValidationErrors.invalidInput("preview", "Invalid PNG header.");
    }

    if (buffer.length > MAX_PREVIEW_SIZE_MB) {
      throw ValidationErrors.invalidInput(
        "preview",
        "Image is too large. Maximum size is 1MB.",
      );
    }
  } catch (error) {
    if (error instanceof Error && error.message.includes("Invalid PNG")) {
      throw error;
    }
    throw ValidationErrors.invalidInput(
      "preview",
      "Invalid base64 encoding or corrupted image data.",
    );
  }
}

export const CreateInvitationSchema = z.object({
  email: z.string().email("Invalid email address"),
  orgId: z.string().uuid("Invalid organization ID"),
  role: z.enum(["owner", "admin"]).default("admin"),
});

export const AcceptInvitationSchema = z.object({
  invitationId: z.string().uuid("Invalid invitation ID"),
});

export const RevokeInvitationSchema = z.object({
  invitationId: z.string().uuid("Invalid invitation ID"),
});

export const RemoveMemberSchema = z.object({
  orgId: z.string().uuid("Invalid organization ID"),
  userId: z.string().uuid("Invalid user ID"),
});

export const UpdateMemberRoleSchema = z.object({
  orgId: z.string().uuid("Invalid organization ID"),
  userId: z.string().uuid("Invalid user ID"),
  role: z.enum(["owner", "admin"]),
});

export const AddUserByEmailSchema = z.object({
  orgId: z.string().uuid("Invalid organization ID"),
  email: z.string().email("Invalid email address"),
  role: z.enum(["owner", "admin"]),
});

export const CreateNotebookSchema = z.object({
  orgId: z.string().uuid("Invalid organization ID"),
  name: z.string().min(1, "Notebook name is required"),
  description: z.string().optional(),
});

export const UpdateNotebookSchema = z.object({
  id: z.string().uuid("Invalid notebook ID"),
  name: z.string().min(1).optional(),
  description: z.string().optional(),
});

export const SaveNotebookPreviewSchema = z.object({
  notebookId: z.string().uuid("Invalid notebook ID"),
  preview: z.string().startsWith("data:image/png;base64,"),
});

export const UpdateDatasetSchema = z.object({
  id: z.string().uuid("Invalid dataset ID"),
  name: z.string().min(1).optional(),
  displayName: z.string().optional(),
  description: z.string().optional(),
  isPublic: z.boolean().optional(),
});

export const CreateDatasetSchema = z.object({
  orgId: z.string().uuid("Invalid organization ID"),
  name: z
    .string()
    .min(1, "Dataset name is required")
    .regex(
      /^[a-zA-Z][a-zA-Z0-9_]+$/,
      "Dataset name can only contain letters, numbers, and underscores",
    ),
  displayName: z.string().min(1, "Display name is required"),
  description: z.string().optional(),
  isPublic: z.boolean().optional(),
  type: z.enum(["USER_MODEL", "DATA_CONNECTOR", "DATA_INGESTION"]),
});

export const CreateModelSchema = z.object({
  orgId: z.string().uuid("Invalid organization ID"),
  datasetId: z.string().uuid("Invalid dataset ID"),
  name: z.string().min(1, "Model name is required"),
  isEnabled: z.boolean().optional(),
});

const ModelColumnSchema = z.object({
  name: z.string(),
  type: z.string(),
  description: z.string().optional(),
});

const ModelDependencySchema = z.object({
  modelId: z.string().uuid(),
  alias: z.string().optional(),
});

const ModelKindOptionsSchema = z.object({
  timeColumn: z.string().optional(),
  timeColumnFormat: z.string().optional(),
  batchSize: z.number().int().optional(),
  lookback: z.number().int().optional(),
  uniqueKeyColumns: z.array(z.string()).optional(),
  whenMatchedSql: z.string().optional(),
  mergeFilter: z.string().optional(),
  validFromName: z.string().optional(),
  validToName: z.string().optional(),
  invalidateHardDeletes: z.boolean().optional(),
  updatedAtColumn: z.string().optional(),
  updatedAtAsValidFrom: z.boolean().optional(),
  scdColumns: z.array(z.string()).optional(),
  executionTimeAsValidFrom: z.boolean().optional(),
});

export const CreateModelRevisionSchema = z.object({
  modelId: z.string().uuid(),
  name: z.string(),
  displayName: z.string(),
  description: z.string().optional(),
  language: z.string(),
  code: z.string(),
  cron: z.string(),
  start: z.string().datetime().optional(),
  end: z.string().datetime().optional(),
  schema: z.array(ModelColumnSchema),
  dependsOn: z.array(ModelDependencySchema).optional(),
  partitionedBy: z.array(z.string()).optional(),
  clusteredBy: z.array(z.string()).optional(),
  kind: z.enum([
    "INCREMENTAL_BY_TIME_RANGE",
    "INCREMENTAL_BY_UNIQUE_KEY",
    "INCREMENTAL_BY_PARTITION",
    "SCD_TYPE_2_BY_TIME",
    "SCD_TYPE_2_BY_COLUMN",
    "FULL",
    "VIEW",
  ]),
  kindOptions: ModelKindOptionsSchema.optional(),
});

export const CreateModelReleaseSchema = z.object({
  modelId: z.string().uuid(),
  modelRevisionId: z.string().uuid(),
  description: z.string().optional(),
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
