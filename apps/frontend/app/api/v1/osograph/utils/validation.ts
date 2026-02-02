import { z } from "zod";
import { ValidationErrors } from "@/app/api/v1/osograph/utils/errors";
import type { ValidTableName } from "@/app/api/v1/osograph/utils/query-builder";
import { DATASET_TYPES } from "@/lib/types/dataset";
import {
  ConnectorType,
  DYNAMIC_CONNECTOR_NAME_REGEX,
  DYNAMIC_CONNECTOR_VALUES_REGEX,
} from "@/lib/types/dynamic-connector";

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

export const CreateStaticModelSchema = z.object({
  orgId: z.string().uuid("Invalid organization ID"),
  datasetId: z.string().uuid("Invalid dataset ID"),
  name: z
    .string()
    .min(1, "StaticModel name is required")
    .regex(
      NAME_REGEX,
      "StaticModel name can only contain letters, numbers, and underscores",
    ),
});

export const UpdateStaticModelSchema = z.object({
  staticModelId: z.string().uuid("Invalid static model ID"),
  name: z
    .string()
    .min(1)
    .regex(
      NAME_REGEX,
      "StaticModel name can only contain letters, numbers, and underscores",
    )
    .optional(),
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

export const CreateDataIngestionSchema = z.object({
  datasetId: z.string().uuid(),
  factoryType: z.enum(["REST", "GRAPHQL", "ARCHIVE_DIR"]),
  config: z.record(z.any()),
});

const BaseDataConnectionSchema = {
  orgId: z.string().uuid("Invalid organization ID"),
  name: z
    .string()
    .min(1, "DataConnection name is required")
    .regex(
      DYNAMIC_CONNECTOR_NAME_REGEX,
      "DataConnection name can only contain letters, numbers, and underscores",
    ),
};

export const CreateDataConnectionSchema = z.discriminatedUnion("type", [
  z.object({
    ...BaseDataConnectionSchema,
    type: z
      .literal("POSTGRESQL")
      .transform(() => "postgresql" as ConnectorType),
    config: z
      .object({
        "connection-url": z.string().regex(DYNAMIC_CONNECTOR_VALUES_REGEX),
        "connection-user": z.string().regex(DYNAMIC_CONNECTOR_VALUES_REGEX),
      })
      .strict(),
    credentials: z
      .object({
        "connection-password": z.string().regex(DYNAMIC_CONNECTOR_VALUES_REGEX),
      })
      .strict(),
  }),
  z.object({
    ...BaseDataConnectionSchema,
    type: z.literal("GSHEETS").transform(() => "gsheets" as ConnectorType),
    config: z
      .object({
        "metadata-sheet-id": z.string().regex(DYNAMIC_CONNECTOR_VALUES_REGEX),
      })
      .strict(),
    credentials: z
      .object({
        "credentials-key": z.string().regex(DYNAMIC_CONNECTOR_VALUES_REGEX),
      })
      .strict(),
  }),
  z.object({
    ...BaseDataConnectionSchema,
    type: z.literal("BIGQUERY").transform(() => "bigquery" as ConnectorType),
    config: z
      .object({
        "project-id": z.string().regex(DYNAMIC_CONNECTOR_VALUES_REGEX),
      })
      .strict(),
    credentials: z
      .object({
        "credentials-key": z.string().regex(DYNAMIC_CONNECTOR_VALUES_REGEX),
      })
      .strict(),
  }),
]);

export const CreateDataConnectionAliasSchema = z.object({
  dataConnectionId: z.string().uuid(),
  name: z.string(),
  schema: z.string(),
});

const ModelColumnContextSchema = z.object({
  name: z.string(),
  context: z.string(),
});

export const UpdateModelContextSchema = z.object({
  datasetId: z.string().uuid(),
  modelId: z.string(),
  context: z.string().optional(),
  columnContext: z.array(ModelColumnContextSchema).optional(),
});

export const CreateDataIngestionRunRequestSchema = z.object({
  datasetId: z.string().uuid(),
});

export const CreateDataConnectionRunRequestSchema = z.object({
  datasetId: z.string().uuid(),
});

export const CreateStaticModelRunRequestSchema = z.object({
  datasetId: z.string().uuid(),
  selectedModels: z.array(z.string()),
});

export const StartRunSchema = z.object({
  runId: z.string().uuid(),
});

export const UpdateMetadataSchema = z.object({
  value: z.record(z.any()),
  merge: z.boolean().default(false),
});

export const FinishRunSchema = z.object({
  runId: z.string().uuid(),
  status: z.enum(["SUCCESS", "FAILED", "CANCELED"]),
  statusCode: z.number().int(),
  logsUrl: z.string().url(),
  metadata: UpdateMetadataSchema.optional(),
});

export const UpdateRunMetadataSchema = z.object({
  runId: z.string().uuid(),
  metadata: UpdateMetadataSchema,
});

export const StartStepSchema = z.object({
  runId: z.string().uuid(),
  name: z.string(),
  displayName: z.string(),
});

export const FinishStepSchema = z.object({
  stepId: z.string().uuid(),
  status: z.enum(["SUCCESS", "FAILED", "CANCELED"]),
  logsUrl: z.string().url(),
});

export const CreateMaterializationSchema = z.object({
  stepId: z.string().uuid(),
  tableId: z.string(),
  warehouseFqn: z.string(),
  schema: z.array(DataModelColumnSchema),
});

export const SavePublishedNotebookHtmlSchema = z.object({
  notebookId: z.string().uuid(),
  htmlContent: z.string(),
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

export const ErrorDetailsSchema = z.object({
  message: z.string(),
  error_type: z.string(),
  error_name: z.string(),
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
export const StaticModelWhereSchema = createWhereSchema("static_model");
export const DataIngestionsWhereSchema = createWhereSchema("data_ingestions");
export const InvitationWhereSchema = createWhereSchema("invitations");
export const OrganizationWhereSchema = createWhereSchema("organizations");
export const DataModelRevisionWhereSchema = createWhereSchema("model_revision");
export const DataModelReleaseWhereSchema = createWhereSchema("model_release");
export const RunWhereSchema = createWhereSchema("run");
export const StepWhereSchema = createWhereSchema("step");
export const MaterializationWhereSchema = createWhereSchema("materialization");
export const DataConnectionWhereSchema =
  createWhereSchema("dynamic_connectors");

export function validateInput<T>(
  schema: z.ZodType<T, any, any>,
  input: unknown,
): T {
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
