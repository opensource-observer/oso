import { z } from "zod";
import { ValidationErrors } from "@/app/api/v1/osograph/utils/errors";
import type { ValidTableName } from "@/app/api/v1/osograph/utils/query-builder";
import { DATASET_TYPES } from "@/lib/types/dataset";

const NAME_REGEX = /^[a-z][a-z0-9_]*$/;
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
  name: z
    .string()
    .min(1)
    .regex(
      NAME_REGEX,
      "Dataset name can only contain letters, numbers, and underscores",
    )
    .optional(),
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
      NAME_REGEX,
      "Dataset name can only contain letters, numbers, and underscores",
    ),
  displayName: z.string().min(1, "Display name is required"),
  description: z.string().optional(),
  isPublic: z.boolean().optional(),
  type: z.enum(DATASET_TYPES),
});

export const CreateDataModelSchema = z.object({
  orgId: z.string().uuid("Invalid organization ID"),
  datasetId: z.string().uuid("Invalid dataset ID"),
  name: z
    .string()
    .min(1, "DataModel name is required")
    .regex(
      NAME_REGEX,
      "DataModel name can only contain letters, numbers, and underscores",
    ),
  isEnabled: z.boolean().optional(),
});

export const UpdateDataModelSchema = z.object({
  dataModelId: z.string().uuid("Invalid data model ID"),
  name: z
    .string()
    .min(1)
    .regex(
      NAME_REGEX,
      "DataModel name can only contain letters, numbers, and underscores",
    )
    .optional(),
  isEnabled: z.boolean().optional(),
});

const DataModelColumnSchema = z.object({
  name: z.string(),
  type: z.string(),
  description: z.string().optional(),
});

const DataModelDependencySchema = z.object({
  dataModelId: z.string().uuid(),
  alias: z.string().optional(),
});

const DataModelKindOptionsSchema = z.object({
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

export const CreateDataModelRevisionSchema = z.object({
  dataModelId: z.string().uuid(),
  name: z
    .string()
    .regex(
      NAME_REGEX,
      "DataModelRevision name can only contain letters, numbers, and underscores",
    ),
  displayName: z.string(),
  description: z.string().optional(),
  language: z.string(),
  code: z.string(),
  cron: z.string(),
  start: z.date().optional(),
  end: z.date().optional(),
  schema: z.array(DataModelColumnSchema),
  dependsOn: z.array(DataModelDependencySchema).optional(),
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
  kindOptions: DataModelKindOptionsSchema.optional(),
});

export const CreateDataModelReleaseSchema = z.object({
  dataModelId: z.string().uuid(),
  dataModelRevisionId: z.string().uuid(),
  description: z.string().optional(),
});

export const CreateUserModelRunRequestSchema = z.object({
  datasetId: z.string().uuid(),
  selectedModels: z.array(z.string()).optional(),
});

export const CreateDataIngestionRunRequestSchema = z.object({
  datasetId: z.string().uuid(),
});

export const CreateDataConnectorRunRequestSchema = z.object({
  datasetId: z.string().uuid(),
});

export const CreateStaticModelRunRequestSchema = z.object({
  datasetId: z.string().uuid(),
});

export const ResolveTablesSchema = z.object({
  references: z.array(z.string()).min(1, "At least one reference is required"),
  metadata: z
    .object({
      orgName: z.string().optional(),
      datasetName: z.string().optional(),
    })
    .optional(),
});

export const TableMetadataWhereSchema = z.object({
  orgId: z.object({ eq: z.string().uuid() }),
  catalogName: z.object({ eq: z.string() }),
  schemaName: z.object({ eq: z.string() }),
  tableName: z.object({ eq: z.string() }),
});

export function createWhereSchema<T extends ValidTableName>(_tableName: T) {
  const comparisonOperators = z.object({
    eq: z.unknown().optional(),
    neq: z.unknown().optional(),
    gt: z.unknown().optional(),
    gte: z.unknown().optional(),
    lt: z.unknown().optional(),
    lte: z.unknown().optional(),
    in: z.array(z.unknown()).optional(),
    like: z.string().optional(),
    ilike: z.string().optional(),
    is: z.union([z.null(), z.boolean()]).optional(),
  });

  return z.record(z.string(), comparisonOperators).refine(
    (data) => {
      if (Object.keys(data).length === 0) {
        return false;
      }

      for (const [_field, operators] of Object.entries(data)) {
        const hasOperator = Object.values(operators).some(
          (val) => val !== undefined,
        );
        if (!hasOperator) {
          return false;
        }
      }
      return true;
    },
    {
      message:
        "Where clause must have at least one field with at least one operator",
    },
  );
}

export const NotebookWhereSchema = createWhereSchema("notebooks");
export const DatasetWhereSchema = createWhereSchema("datasets");
export const DataModelWhereSchema = createWhereSchema("model");
export const InvitationWhereSchema = createWhereSchema("invitations");
export const OrganizationWhereSchema = createWhereSchema("organizations");
export const DataModelRevisionWhereSchema = createWhereSchema("model_revision");
export const DataModelReleaseWhereSchema = createWhereSchema("model_release");
export const RunWhereSchema = createWhereSchema("run");
export const MaterializationWhereSchema = createWhereSchema("materialization");

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
