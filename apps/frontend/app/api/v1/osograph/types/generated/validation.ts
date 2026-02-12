import { z } from 'zod'
import { AcceptInvitationInput, AddUserByEmailInput, CancelRunInput, CreateDataConnectionDatasetsInput, CreateDataConnectionInput, CreateDataConnectionRunRequestInput, CreateDataIngestionInput, CreateDataIngestionRunRequestInput, CreateDataModelInput, CreateDataModelReleaseInput, CreateDataModelRevisionInput, CreateDatasetInput, CreateInvitationInput, CreateMaterializationInput, CreateNotebookInput, CreateStaticModelInput, CreateStaticModelRunRequestInput, CreateUserModelRunRequestInput, DataConnectionSchemaInput, DataConnectionTableInput, DataConnectionType, DataIngestionFactoryType, DataModelColumnInput, DataModelDependencyInput, DataModelKind, DataModelKindOptionsInput, DatasetType, FinishRunInput, FinishStepInput, InvitationStatus, MemberRole, ModelColumnContextInput, RemoveMemberInput, RevokeInvitationInput, RunStatus, RunTriggerType, RunType, SaveNotebookPreviewInput, SavePublishedNotebookHtmlInput, StartRunInput, StartStepInput, StepStatus, UpdateDataModelInput, UpdateDatasetInput, UpdateMemberRoleInput, UpdateMetadataInput, UpdateModelContextInput, UpdateNotebookInput, UpdateRunMetadataInput, UpdateStaticModelInput } from './types'

type Properties<T> = Required<{
  [K in keyof T]: z.ZodType<T[K], any, T[K]>;
}>;

type definedNonNullAny = {};

export const isDefinedNonNullAny = (v: any): v is definedNonNullAny => v !== undefined && v !== null;

export const definedNonNullAnySchema = z.any().refine((v) => isDefinedNonNullAny(v));

export const DataConnectionTypeSchema = z.nativeEnum(DataConnectionType);

export const DataIngestionFactoryTypeSchema = z.nativeEnum(DataIngestionFactoryType);

export const DataModelKindSchema = z.nativeEnum(DataModelKind);

export const DatasetTypeSchema = z.nativeEnum(DatasetType);

export const InvitationStatusSchema = z.nativeEnum(InvitationStatus);

export const MemberRoleSchema = z.nativeEnum(MemberRole);

export const RunStatusSchema = z.nativeEnum(RunStatus);

export const RunTriggerTypeSchema = z.nativeEnum(RunTriggerType);

export const RunTypeSchema = z.nativeEnum(RunType);

export const StepStatusSchema = z.nativeEnum(StepStatus);

export function AcceptInvitationInputSchema(): z.ZodObject<Properties<AcceptInvitationInput>> {
  return z.object({
    invitationId: z.string()
  })
}

export function AddUserByEmailInputSchema(): z.ZodObject<Properties<AddUserByEmailInput>> {
  return z.object({
    email: z.string(),
    orgId: z.string(),
    role: MemberRoleSchema
  })
}

export function CancelRunInputSchema(): z.ZodObject<Properties<CancelRunInput>> {
  return z.object({
    runId: z.string()
  })
}

export function CreateDataConnectionDatasetsInputSchema(): z.ZodObject<Properties<CreateDataConnectionDatasetsInput>> {
  return z.object({
    dataConnectionId: z.string(),
    orgId: z.string(),
    runId: z.string(),
    schemas: z.array(z.lazy(() => DataConnectionSchemaInputSchema()))
  })
}

export function CreateDataConnectionInputSchema(): z.ZodObject<Properties<CreateDataConnectionInput>> {
  return z.object({
    config: z.record(z.string(), z.unknown()),
    credentials: z.record(z.string(), z.unknown()),
    name: z.string(),
    orgId: z.string(),
    type: DataConnectionTypeSchema
  })
}

export function CreateDataConnectionRunRequestInputSchema(): z.ZodObject<Properties<CreateDataConnectionRunRequestInput>> {
  return z.object({
    datasetId: z.string()
  })
}

export function CreateDataIngestionInputSchema(): z.ZodObject<Properties<CreateDataIngestionInput>> {
  return z.object({
    config: z.record(z.string(), z.unknown()),
    datasetId: z.string(),
    factoryType: DataIngestionFactoryTypeSchema
  })
}

export function CreateDataIngestionRunRequestInputSchema(): z.ZodObject<Properties<CreateDataIngestionRunRequestInput>> {
  return z.object({
    datasetId: z.string()
  })
}

export function CreateDataModelInputSchema(): z.ZodObject<Properties<CreateDataModelInput>> {
  return z.object({
    datasetId: z.string(),
    isEnabled: z.boolean().nullish(),
    name: z.string(),
    orgId: z.string()
  })
}

export function CreateDataModelReleaseInputSchema(): z.ZodObject<Properties<CreateDataModelReleaseInput>> {
  return z.object({
    dataModelId: z.string(),
    dataModelRevisionId: z.string(),
    description: z.string().nullish()
  })
}

export function CreateDataModelRevisionInputSchema(): z.ZodObject<Properties<CreateDataModelRevisionInput>> {
  return z.object({
    clusteredBy: z.array(z.string()).nullish(),
    code: z.string(),
    cron: z.string(),
    dataModelId: z.string(),
    dependsOn: z.array(z.lazy(() => DataModelDependencyInputSchema())).nullish(),
    description: z.string().nullish(),
    end: z.date().nullish(),
    kind: DataModelKindSchema,
    kindOptions: z.lazy(() => DataModelKindOptionsInputSchema().nullish()),
    language: z.string(),
    name: z.string(),
    partitionedBy: z.array(z.string()).nullish(),
    schema: z.array(z.lazy(() => DataModelColumnInputSchema())),
    start: z.date().nullish()
  })
}

export function CreateDatasetInputSchema(): z.ZodObject<Properties<CreateDatasetInput>> {
  return z.object({
    description: z.string().nullish(),
    displayName: z.string().nullish(),
    name: z.string(),
    orgId: z.string(),
    type: DatasetTypeSchema.default("USER_MODEL").nullish()
  })
}

export function CreateInvitationInputSchema(): z.ZodObject<Properties<CreateInvitationInput>> {
  return z.object({
    email: z.string(),
    orgId: z.string(),
    role: MemberRoleSchema.default("admin")
  })
}

export function CreateMaterializationInputSchema(): z.ZodObject<Properties<CreateMaterializationInput>> {
  return z.object({
    schema: z.array(z.lazy(() => DataModelColumnInputSchema())),
    stepId: z.string(),
    tableId: z.string(),
    warehouseFqn: z.string()
  })
}

export function CreateNotebookInputSchema(): z.ZodObject<Properties<CreateNotebookInput>> {
  return z.object({
    description: z.string().nullish(),
    name: z.string(),
    orgId: z.string()
  })
}

export function CreateStaticModelInputSchema(): z.ZodObject<Properties<CreateStaticModelInput>> {
  return z.object({
    datasetId: z.string(),
    name: z.string(),
    orgId: z.string()
  })
}

export function CreateStaticModelRunRequestInputSchema(): z.ZodObject<Properties<CreateStaticModelRunRequestInput>> {
  return z.object({
    datasetId: z.string(),
    selectedModels: z.array(z.string()).nullish()
  })
}

export function CreateUserModelRunRequestInputSchema(): z.ZodObject<Properties<CreateUserModelRunRequestInput>> {
  return z.object({
    datasetId: z.string(),
    selectedModels: z.array(z.string()).nullish()
  })
}

export function DataConnectionSchemaInputSchema(): z.ZodObject<Properties<DataConnectionSchemaInput>> {
  return z.object({
    name: z.string(),
    tables: z.array(z.lazy(() => DataConnectionTableInputSchema()))
  })
}

export function DataConnectionTableInputSchema(): z.ZodObject<Properties<DataConnectionTableInput>> {
  return z.object({
    name: z.string(),
    schema: z.array(z.lazy(() => DataModelColumnInputSchema()))
  })
}

export function DataModelColumnInputSchema(): z.ZodObject<Properties<DataModelColumnInput>> {
  return z.object({
    description: z.string().nullish(),
    name: z.string(),
    type: z.string()
  })
}

export function DataModelDependencyInputSchema(): z.ZodObject<Properties<DataModelDependencyInput>> {
  return z.object({
    alias: z.string().nullish(),
    dataModelId: z.string()
  })
}

export function DataModelKindOptionsInputSchema(): z.ZodObject<Properties<DataModelKindOptionsInput>> {
  return z.object({
    batchSize: z.number().nullish(),
    executionTimeAsValidFrom: z.boolean().nullish(),
    invalidateHardDeletes: z.boolean().nullish(),
    lookback: z.number().nullish(),
    mergeFilter: z.string().nullish(),
    scdColumns: z.array(z.string()).nullish(),
    timeColumn: z.string().nullish(),
    timeColumnFormat: z.string().nullish(),
    uniqueKeyColumns: z.array(z.string()).nullish(),
    updatedAtAsValidFrom: z.boolean().nullish(),
    updatedAtColumn: z.string().nullish(),
    validFromName: z.string().nullish(),
    validToName: z.string().nullish(),
    whenMatchedSql: z.string().nullish()
  })
}

export function FinishRunInputSchema(): z.ZodObject<Properties<FinishRunInput>> {
  return z.object({
    logsUrl: z.string(),
    metadata: z.lazy(() => UpdateMetadataInputSchema().nullish()),
    runId: z.string(),
    status: RunStatusSchema,
    statusCode: z.number()
  })
}

export function FinishStepInputSchema(): z.ZodObject<Properties<FinishStepInput>> {
  return z.object({
    logsUrl: z.string(),
    status: StepStatusSchema,
    stepId: z.string()
  })
}

export function ModelColumnContextInputSchema(): z.ZodObject<Properties<ModelColumnContextInput>> {
  return z.object({
    context: z.string(),
    name: z.string()
  })
}

export function RemoveMemberInputSchema(): z.ZodObject<Properties<RemoveMemberInput>> {
  return z.object({
    orgId: z.string(),
    userId: z.string()
  })
}

export function RevokeInvitationInputSchema(): z.ZodObject<Properties<RevokeInvitationInput>> {
  return z.object({
    invitationId: z.string(),
    orgId: z.string()
  })
}

export function SaveNotebookPreviewInputSchema(): z.ZodObject<Properties<SaveNotebookPreviewInput>> {
  return z.object({
    notebookId: z.string(),
    preview: z.string()
  })
}

export function SavePublishedNotebookHtmlInputSchema(): z.ZodObject<Properties<SavePublishedNotebookHtmlInput>> {
  return z.object({
    htmlContent: z.string(),
    notebookId: z.string()
  })
}

export function StartRunInputSchema(): z.ZodObject<Properties<StartRunInput>> {
  return z.object({
    runId: z.string()
  })
}

export function StartStepInputSchema(): z.ZodObject<Properties<StartStepInput>> {
  return z.object({
    displayName: z.string(),
    name: z.string(),
    runId: z.string()
  })
}

export function UpdateDataModelInputSchema(): z.ZodObject<Properties<UpdateDataModelInput>> {
  return z.object({
    dataModelId: z.string(),
    isEnabled: z.boolean().nullish(),
    name: z.string().nullish()
  })
}

export function UpdateDatasetInputSchema(): z.ZodObject<Properties<UpdateDatasetInput>> {
  return z.object({
    description: z.string().nullish(),
    displayName: z.string().nullish(),
    id: z.string(),
    name: z.string().nullish()
  })
}

export function UpdateMemberRoleInputSchema(): z.ZodObject<Properties<UpdateMemberRoleInput>> {
  return z.object({
    orgId: z.string(),
    role: MemberRoleSchema,
    userId: z.string()
  })
}

export function UpdateMetadataInputSchema(): z.ZodObject<Properties<UpdateMetadataInput>> {
  return z.object({
    merge: z.boolean().default(false).nullish(),
    value: z.record(z.string(), z.unknown())
  })
}

export function UpdateModelContextInputSchema(): z.ZodObject<Properties<UpdateModelContextInput>> {
  return z.object({
    columnContext: z.array(z.lazy(() => ModelColumnContextInputSchema())).nullish(),
    context: z.string().nullish(),
    datasetId: z.string(),
    modelId: z.string()
  })
}

export function UpdateNotebookInputSchema(): z.ZodObject<Properties<UpdateNotebookInput>> {
  return z.object({
    description: z.string().nullish(),
    id: z.string(),
    name: z.string().nullish()
  })
}

export function UpdateRunMetadataInputSchema(): z.ZodObject<Properties<UpdateRunMetadataInput>> {
  return z.object({
    metadata: z.lazy(() => UpdateMetadataInputSchema()),
    runId: z.string()
  })
}

export function UpdateStaticModelInputSchema(): z.ZodObject<Properties<UpdateStaticModelInput>> {
  return z.object({
    name: z.string().nullish(),
    staticModelId: z.string()
  })
}
