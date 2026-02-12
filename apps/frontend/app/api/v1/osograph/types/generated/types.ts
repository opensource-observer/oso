import { GraphQLResolveInfo, GraphQLScalarType, GraphQLScalarTypeConfig } from 'graphql';
import { DataConnectionAliasRow, DataIngestionsRow, DatasetsRow, OrganizationsRow, ModelRow, ModelRevisionRow, ModelReleaseRow, InvitationsRow, ModelContextsRow, NotebooksRow, RunRow, StepRow, MaterializationRow, StaticModelRow, UserProfilesRow } from '@/lib/types/schema-types';
import { GraphQLContext } from '@/app/api/v1/osograph/types/context';
export type Maybe<T> = T | null;
export type InputMaybe<T> = Maybe<T>;
export type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
export type MakeOptional<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]?: Maybe<T[SubKey]> };
export type MakeMaybe<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]: Maybe<T[SubKey]> };
export type MakeEmpty<T extends { [key: string]: unknown }, K extends keyof T> = { [_ in K]?: never };
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
export type Omit<T, K extends keyof T> = Pick<T, Exclude<keyof T, K>>;
export type RequireFields<T, K extends keyof T> = Omit<T, K> & { [P in K]-?: NonNullable<T[P]> };
/** All built-in and custom scalars, mapped to their actual values */
export type Scalars = {
  ID: { input: string; output: string; }
  String: { input: string; output: string; }
  Boolean: { input: boolean; output: boolean; }
  Int: { input: number; output: number; }
  Float: { input: number; output: number; }
  DateTime: { input: Date; output: Date; }
  JSON: { input: object; output: object; }
};

export type AcceptInvitationInput = {
  invitationId: Scalars['ID']['input'];
};

export type AcceptInvitationPayload = {
  __typename?: 'AcceptInvitationPayload';
  member?: Maybe<OrganizationMember>;
  message?: Maybe<Scalars['String']['output']>;
  success: Scalars['Boolean']['output'];
};

export type AddUserByEmailInput = {
  email: Scalars['String']['input'];
  orgId: Scalars['ID']['input'];
  role: MemberRole;
};

export type AddUserByEmailPayload = {
  __typename?: 'AddUserByEmailPayload';
  member?: Maybe<OrganizationMember>;
  message?: Maybe<Scalars['String']['output']>;
  success: Scalars['Boolean']['output'];
};

export type CancelRunInput = {
  runId: Scalars['ID']['input'];
};

export type CancelRunPayload = {
  __typename?: 'CancelRunPayload';
  message?: Maybe<Scalars['String']['output']>;
  run?: Maybe<Run>;
  success: Scalars['Boolean']['output'];
};

export type CreateDataConnectionDatasetsInput = {
  dataConnectionId: Scalars['ID']['input'];
  orgId: Scalars['ID']['input'];
  runId: Scalars['ID']['input'];
  schemas: Array<DataConnectionSchemaInput>;
};

export type CreateDataConnectionInput = {
  config: Scalars['JSON']['input'];
  credentials: Scalars['JSON']['input'];
  name: Scalars['String']['input'];
  orgId: Scalars['ID']['input'];
  type: DataConnectionType;
};

export type CreateDataConnectionPayload = {
  __typename?: 'CreateDataConnectionPayload';
  dataConnection?: Maybe<DataConnection>;
  message?: Maybe<Scalars['String']['output']>;
  success: Scalars['Boolean']['output'];
};

export type CreateDataConnectionRunRequestInput = {
  datasetId: Scalars['ID']['input'];
};

export type CreateDataIngestionInput = {
  config: Scalars['JSON']['input'];
  datasetId: Scalars['ID']['input'];
  factoryType: DataIngestionFactoryType;
};

export type CreateDataIngestionRunRequestInput = {
  datasetId: Scalars['ID']['input'];
};

export type CreateDataModelInput = {
  datasetId: Scalars['ID']['input'];
  isEnabled?: InputMaybe<Scalars['Boolean']['input']>;
  name: Scalars['String']['input'];
  orgId: Scalars['ID']['input'];
};

export type CreateDataModelPayload = {
  __typename?: 'CreateDataModelPayload';
  dataModel?: Maybe<DataModel>;
  message?: Maybe<Scalars['String']['output']>;
  success: Scalars['Boolean']['output'];
};

export type CreateDataModelReleaseInput = {
  dataModelId: Scalars['ID']['input'];
  dataModelRevisionId: Scalars['ID']['input'];
  description?: InputMaybe<Scalars['String']['input']>;
};

export type CreateDataModelReleasePayload = {
  __typename?: 'CreateDataModelReleasePayload';
  dataModelRelease?: Maybe<DataModelRelease>;
  message?: Maybe<Scalars['String']['output']>;
  success: Scalars['Boolean']['output'];
};

export type CreateDataModelRevisionInput = {
  clusteredBy?: InputMaybe<Array<Scalars['String']['input']>>;
  code: Scalars['String']['input'];
  cron: Scalars['String']['input'];
  dataModelId: Scalars['ID']['input'];
  dependsOn?: InputMaybe<Array<DataModelDependencyInput>>;
  description?: InputMaybe<Scalars['String']['input']>;
  end?: InputMaybe<Scalars['DateTime']['input']>;
  kind: DataModelKind;
  kindOptions?: InputMaybe<DataModelKindOptionsInput>;
  language: Scalars['String']['input'];
  name: Scalars['String']['input'];
  partitionedBy?: InputMaybe<Array<Scalars['String']['input']>>;
  schema: Array<DataModelColumnInput>;
  start?: InputMaybe<Scalars['DateTime']['input']>;
};

export type CreateDataModelRevisionPayload = {
  __typename?: 'CreateDataModelRevisionPayload';
  dataModelRevision?: Maybe<DataModelRevision>;
  message?: Maybe<Scalars['String']['output']>;
  success: Scalars['Boolean']['output'];
};

export type CreateDatasetInput = {
  /** The description of the dataset. */
  description?: InputMaybe<Scalars['String']['input']>;
  /** The display name of the dataset. */
  displayName?: InputMaybe<Scalars['String']['input']>;
  /** The name of the dataset. This must be unique within the organization. */
  name: Scalars['String']['input'];
  /** The organization ID the dataset belongs to */
  orgId: Scalars['ID']['input'];
  /**
   * The type of the dataset.
   *
   * Types:
   *   * USER_MODEL: Sometimes called a UDM, this dataset type contains
   *     user-defined data models.
   *   * DATA_INGESTION: This dataset type is used for datasets that are ingested
   *     from external sources using strategies like REST/GraphQL APIs, file
   *     uploads, etc.
   *   * STATIC_MODEL: This is used for datasets composed of statically uploaded
   *     models. Currently only CSV files are supported for static models.
   */
  type?: InputMaybe<DatasetType>;
};

export type CreateDatasetPayload = {
  __typename?: 'CreateDatasetPayload';
  dataset?: Maybe<Dataset>;
  message?: Maybe<Scalars['String']['output']>;
  success: Scalars['Boolean']['output'];
};

export type CreateInvitationInput = {
  email: Scalars['String']['input'];
  orgId: Scalars['ID']['input'];
  role?: MemberRole;
};

export type CreateInvitationPayload = {
  __typename?: 'CreateInvitationPayload';
  invitation?: Maybe<Invitation>;
  message?: Maybe<Scalars['String']['output']>;
  success: Scalars['Boolean']['output'];
};

export type CreateMaterializationInput = {
  schema: Array<DataModelColumnInput>;
  stepId: Scalars['ID']['input'];
  tableId: Scalars['ID']['input'];
  warehouseFqn: Scalars['String']['input'];
};

export type CreateMaterializationPayload = {
  __typename?: 'CreateMaterializationPayload';
  materialization: Materialization;
  message?: Maybe<Scalars['String']['output']>;
  success: Scalars['Boolean']['output'];
};

export type CreateNotebookInput = {
  description?: InputMaybe<Scalars['String']['input']>;
  name: Scalars['String']['input'];
  orgId: Scalars['ID']['input'];
};

export type CreateNotebookPayload = {
  __typename?: 'CreateNotebookPayload';
  message?: Maybe<Scalars['String']['output']>;
  notebook?: Maybe<Notebook>;
  success: Scalars['Boolean']['output'];
};

export type CreateRunRequestPayload = {
  __typename?: 'CreateRunRequestPayload';
  message?: Maybe<Scalars['String']['output']>;
  /**
   * The run that was created as a result of the run request. The response from the
   * `*RunRequest` mutations kick off asynchronous processes. It is possible for
   * the run creation to succeed but for the run to ultimately fail due to errors
   * encountered during the asynchronous execution. Therefore, the `success` field
   * in the payload only indicates whether the run request was successfully
   * created, not whether the run itself was successful. Retrieve the run by
   * querying for runs within a dataset to check the status and results of the run.
   */
  run: Run;
  success: Scalars['Boolean']['output'];
};

export type CreateStaticModelInput = {
  /** The ID of the dataset associated with the static model. */
  datasetId: Scalars['ID']['input'];
  /** The desired name for the static model (must be unique within the organization). */
  name: Scalars['String']['input'];
  /** The ID of the organization to which the static model belongs. */
  orgId: Scalars['ID']['input'];
};

export type CreateStaticModelPayload = {
  __typename?: 'CreateStaticModelPayload';
  message?: Maybe<Scalars['String']['output']>;
  staticModel?: Maybe<StaticModel>;
  success: Scalars['Boolean']['output'];
};

export type CreateStaticModelRunRequestInput = {
  /** The ID of the static model dataset to run. */
  datasetId: Scalars['ID']['input'];
  /**
   * For static model runs, users can optionally specify a list of model IDs to
   * run. If not provided, all models will be run.
   */
  selectedModels?: InputMaybe<Array<Scalars['String']['input']>>;
};

export type CreateUserModelRunRequestInput = {
  /** The ID of the dataset to run. This must be a USER_MODEL dataset. */
  datasetId: Scalars['ID']['input'];
  /**
   * For user model runs, users can optionally specify a list of data model release
   * IDs to run. If not provided, all models will be run in topological order based
   * on dependencies.
   */
  selectedModels?: InputMaybe<Array<Scalars['String']['input']>>;
};

export type DataConnection = {
  __typename?: 'DataConnection';
  config: Scalars['JSON']['output'];
  createdAt: Scalars['DateTime']['output'];
  id: Scalars['ID']['output'];
  name: Scalars['String']['output'];
  orgId: Scalars['ID']['output'];
  organization: Organization;
  type: DataConnectionType;
  updatedAt: Scalars['DateTime']['output'];
};

export type DataConnectionAlias = {
  __typename?: 'DataConnectionAlias';
  dataConnectionId: Scalars['ID']['output'];
  datasetId: Scalars['ID']['output'];
  id: Scalars['ID']['output'];
  materializations: MaterializationConnection;
  modelContext?: Maybe<ModelContext>;
  orgId: Scalars['ID']['output'];
  previewData: PreviewData;
  schema: Scalars['String']['output'];
};


export type DataConnectionAliasMaterializationsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  single?: InputMaybe<Scalars['Boolean']['input']>;
  tableName: Scalars['String']['input'];
  where?: InputMaybe<Scalars['JSON']['input']>;
};


export type DataConnectionAliasModelContextArgs = {
  tableName: Scalars['String']['input'];
};


export type DataConnectionAliasPreviewDataArgs = {
  tableName: Scalars['String']['input'];
};

export type DataConnectionConnection = {
  __typename?: 'DataConnectionConnection';
  edges: Array<DataConnectionEdge>;
  pageInfo: PageInfo;
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type DataConnectionDefinition = {
  __typename?: 'DataConnectionDefinition';
  /**
   * If the dataset is of type DATA_CONNECTION, this field will contain the data connection model
   * associated with the dataset.
   */
  dataConnectionAlias: DataConnectionAlias;
  datasetId: Scalars['ID']['output'];
  orgId: Scalars['ID']['output'];
};

export type DataConnectionEdge = {
  __typename?: 'DataConnectionEdge';
  cursor: Scalars['String']['output'];
  node: DataConnection;
};

export type DataConnectionSchema = {
  __typename?: 'DataConnectionSchema';
  name: Scalars['String']['output'];
  tables: Array<DataConnectionTable>;
};

export type DataConnectionSchemaInput = {
  name: Scalars['String']['input'];
  tables: Array<DataConnectionTableInput>;
};

export type DataConnectionTable = {
  __typename?: 'DataConnectionTable';
  name: Scalars['String']['output'];
  schema: Array<DataModelColumn>;
};

export type DataConnectionTableInput = {
  name: Scalars['String']['input'];
  schema: Array<DataModelColumnInput>;
};

export const DataConnectionType = {
  Bigquery: 'BIGQUERY',
  Gsheets: 'GSHEETS',
  Postgresql: 'POSTGRESQL'
} as const;

export type DataConnectionType = typeof DataConnectionType[keyof typeof DataConnectionType];
export type DataIngestion = {
  __typename?: 'DataIngestion';
  config: Scalars['JSON']['output'];
  createdAt: Scalars['DateTime']['output'];
  datasetId: Scalars['ID']['output'];
  factoryType: DataIngestionFactoryType;
  id: Scalars['ID']['output'];
  materializations: MaterializationConnection;
  modelContext?: Maybe<ModelContext>;
  orgId: Scalars['ID']['output'];
  previewData: PreviewData;
  updatedAt: Scalars['DateTime']['output'];
};


export type DataIngestionMaterializationsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  single?: InputMaybe<Scalars['Boolean']['input']>;
  tableName: Scalars['String']['input'];
  where?: InputMaybe<Scalars['JSON']['input']>;
};


export type DataIngestionModelContextArgs = {
  tableName: Scalars['String']['input'];
};


export type DataIngestionPreviewDataArgs = {
  tableName: Scalars['String']['input'];
};

export type DataIngestionConnection = {
  __typename?: 'DataIngestionConnection';
  edges: Array<DataIngestionEdge>;
  pageInfo: PageInfo;
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type DataIngestionDefinition = {
  __typename?: 'DataIngestionDefinition';
  /**
   * The data ingestion configuration for this dataset.
   * Unlike DataModels and StaticModels, only one ingestion config is allowed per dataset.
   * Returns null if no configuration has been created yet.
   */
  dataIngestion?: Maybe<DataIngestion>;
  datasetId: Scalars['ID']['output'];
  orgId: Scalars['ID']['output'];
};

export type DataIngestionEdge = {
  __typename?: 'DataIngestionEdge';
  cursor: Scalars['String']['output'];
  node: DataIngestion;
};

export const DataIngestionFactoryType = {
  ArchiveDir: 'ARCHIVE_DIR',
  Graphql: 'GRAPHQL',
  Rest: 'REST'
} as const;

export type DataIngestionFactoryType = typeof DataIngestionFactoryType[keyof typeof DataIngestionFactoryType];
export type DataModel = {
  __typename?: 'DataModel';
  createdAt: Scalars['DateTime']['output'];
  dataset: Dataset;
  id: Scalars['ID']['output'];
  isEnabled: Scalars['Boolean']['output'];
  latestRelease?: Maybe<DataModelRelease>;
  latestRevision?: Maybe<DataModelRevision>;
  materializations: MaterializationConnection;
  modelContext?: Maybe<ModelContext>;
  name: Scalars['String']['output'];
  orgId: Scalars['ID']['output'];
  organization: Organization;
  previewData: PreviewData;
  releases: DataModelReleaseConnection;
  revisions: DataModelRevisionConnection;
  runs: RunConnection;
  updatedAt: Scalars['DateTime']['output'];
};


export type DataModelMaterializationsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  single?: InputMaybe<Scalars['Boolean']['input']>;
  where?: InputMaybe<Scalars['JSON']['input']>;
};


export type DataModelReleasesArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  single?: InputMaybe<Scalars['Boolean']['input']>;
  where?: InputMaybe<Scalars['JSON']['input']>;
};


export type DataModelRevisionsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  single?: InputMaybe<Scalars['Boolean']['input']>;
  where?: InputMaybe<Scalars['JSON']['input']>;
};


export type DataModelRunsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
};

export type DataModelColumn = {
  __typename?: 'DataModelColumn';
  description?: Maybe<Scalars['String']['output']>;
  name: Scalars['String']['output'];
  type: Scalars['String']['output'];
};

export type DataModelColumnInput = {
  description?: InputMaybe<Scalars['String']['input']>;
  name: Scalars['String']['input'];
  type: Scalars['String']['input'];
};

export type DataModelConnection = {
  __typename?: 'DataModelConnection';
  edges: Array<DataModelEdge>;
  pageInfo: PageInfo;
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type DataModelDefinition = {
  __typename?: 'DataModelDefinition';
  /**
   * If the dataset is of type USER_MODEL, this field will contain the list of data models
   * associated with the dataset. Otherwise it will be an empty list.
   */
  dataModels: DataModelConnection;
  datasetId: Scalars['ID']['output'];
  orgId: Scalars['ID']['output'];
};


export type DataModelDefinitionDataModelsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  single?: InputMaybe<Scalars['Boolean']['input']>;
  where?: InputMaybe<Scalars['JSON']['input']>;
};

export type DataModelDependency = {
  __typename?: 'DataModelDependency';
  alias?: Maybe<Scalars['String']['output']>;
  tableId: Scalars['ID']['output'];
};

export type DataModelDependencyInput = {
  alias?: InputMaybe<Scalars['String']['input']>;
  dataModelId: Scalars['ID']['input'];
};

export type DataModelEdge = {
  __typename?: 'DataModelEdge';
  cursor: Scalars['String']['output'];
  node: DataModel;
};

export const DataModelKind = {
  Full: 'FULL',
  IncrementalByPartition: 'INCREMENTAL_BY_PARTITION',
  IncrementalByTimeRange: 'INCREMENTAL_BY_TIME_RANGE',
  IncrementalByUniqueKey: 'INCREMENTAL_BY_UNIQUE_KEY',
  ScdType_2ByColumn: 'SCD_TYPE_2_BY_COLUMN',
  ScdType_2ByTime: 'SCD_TYPE_2_BY_TIME',
  View: 'VIEW'
} as const;

export type DataModelKind = typeof DataModelKind[keyof typeof DataModelKind];
export type DataModelKindOptions = {
  __typename?: 'DataModelKindOptions';
  batchSize?: Maybe<Scalars['Int']['output']>;
  executionTimeAsValidFrom?: Maybe<Scalars['Boolean']['output']>;
  invalidateHardDeletes?: Maybe<Scalars['Boolean']['output']>;
  lookback?: Maybe<Scalars['Int']['output']>;
  mergeFilter?: Maybe<Scalars['String']['output']>;
  scdColumns?: Maybe<Array<Scalars['String']['output']>>;
  timeColumn?: Maybe<Scalars['String']['output']>;
  timeColumnFormat?: Maybe<Scalars['String']['output']>;
  uniqueKeyColumns?: Maybe<Array<Scalars['String']['output']>>;
  updatedAtAsValidFrom?: Maybe<Scalars['Boolean']['output']>;
  updatedAtColumn?: Maybe<Scalars['String']['output']>;
  validFromName?: Maybe<Scalars['String']['output']>;
  validToName?: Maybe<Scalars['String']['output']>;
  whenMatchedSql?: Maybe<Scalars['String']['output']>;
};

export type DataModelKindOptionsInput = {
  batchSize?: InputMaybe<Scalars['Int']['input']>;
  executionTimeAsValidFrom?: InputMaybe<Scalars['Boolean']['input']>;
  invalidateHardDeletes?: InputMaybe<Scalars['Boolean']['input']>;
  lookback?: InputMaybe<Scalars['Int']['input']>;
  mergeFilter?: InputMaybe<Scalars['String']['input']>;
  scdColumns?: InputMaybe<Array<Scalars['String']['input']>>;
  timeColumn?: InputMaybe<Scalars['String']['input']>;
  timeColumnFormat?: InputMaybe<Scalars['String']['input']>;
  uniqueKeyColumns?: InputMaybe<Array<Scalars['String']['input']>>;
  updatedAtAsValidFrom?: InputMaybe<Scalars['Boolean']['input']>;
  updatedAtColumn?: InputMaybe<Scalars['String']['input']>;
  validFromName?: InputMaybe<Scalars['String']['input']>;
  validToName?: InputMaybe<Scalars['String']['input']>;
  whenMatchedSql?: InputMaybe<Scalars['String']['input']>;
};

export type DataModelRelease = {
  __typename?: 'DataModelRelease';
  createdAt: Scalars['DateTime']['output'];
  dataModel: DataModel;
  dataModelId: Scalars['ID']['output'];
  description?: Maybe<Scalars['String']['output']>;
  id: Scalars['ID']['output'];
  orgId: Scalars['ID']['output'];
  organization: Organization;
  revision: DataModelRevision;
  revisionId: Scalars['ID']['output'];
  updatedAt: Scalars['DateTime']['output'];
};

export type DataModelReleaseConnection = {
  __typename?: 'DataModelReleaseConnection';
  edges: Array<DataModelReleaseEdge>;
  pageInfo: PageInfo;
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type DataModelReleaseEdge = {
  __typename?: 'DataModelReleaseEdge';
  cursor: Scalars['String']['output'];
  node: DataModelRelease;
};

export type DataModelRevision = {
  __typename?: 'DataModelRevision';
  clusteredBy?: Maybe<Array<Scalars['String']['output']>>;
  code: Scalars['String']['output'];
  createdAt: Scalars['DateTime']['output'];
  cron: Scalars['String']['output'];
  dataModel: DataModel;
  dataModelId: Scalars['ID']['output'];
  dependsOn?: Maybe<Array<DataModelDependency>>;
  description?: Maybe<Scalars['String']['output']>;
  end?: Maybe<Scalars['DateTime']['output']>;
  hash: Scalars['String']['output'];
  id: Scalars['ID']['output'];
  kind: DataModelKind;
  kindOptions?: Maybe<DataModelKindOptions>;
  language: Scalars['String']['output'];
  name: Scalars['String']['output'];
  orgId: Scalars['ID']['output'];
  organization: Organization;
  partitionedBy?: Maybe<Array<Scalars['String']['output']>>;
  revisionNumber: Scalars['Int']['output'];
  schema?: Maybe<Array<DataModelColumn>>;
  start?: Maybe<Scalars['DateTime']['output']>;
};

export type DataModelRevisionConnection = {
  __typename?: 'DataModelRevisionConnection';
  edges: Array<DataModelRevisionEdge>;
  pageInfo: PageInfo;
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type DataModelRevisionEdge = {
  __typename?: 'DataModelRevisionEdge';
  cursor: Scalars['String']['output'];
  node: DataModelRevision;
};

export type Dataset = {
  __typename?: 'Dataset';
  createdAt: Scalars['DateTime']['output'];
  creator: User;
  creatorId: Scalars['ID']['output'];
  description?: Maybe<Scalars['String']['output']>;
  displayName?: Maybe<Scalars['String']['output']>;
  id: Scalars['ID']['output'];
  /**
   * The materializations for this dataset. Returns all materializations regardless of their source
   * (data model, static model, or data ingestion).
   */
  materializations: MaterializationConnection;
  name: Scalars['String']['output'];
  orgId: Scalars['ID']['output'];
  organization: Organization;
  /**
   * The runs for this dataset. For USER_MODEL datasets, each run is related to individual data models.
   * FOR DATA_INGESTION datasets, each run is related to individual ingestion jobs.
   * For DATA_CONNECTION datasets, runs are not applicable and this field will be an empty list.
   */
  runs: RunConnection;
  tables: TableConnection;
  type: DatasetType;
  typeDefinition: DatasetTypeDefinition;
  updatedAt: Scalars['DateTime']['output'];
};


export type DatasetMaterializationsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  single?: InputMaybe<Scalars['Boolean']['input']>;
  where?: InputMaybe<Scalars['JSON']['input']>;
};


export type DatasetRunsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  single?: InputMaybe<Scalars['Boolean']['input']>;
  where?: InputMaybe<Scalars['JSON']['input']>;
};


export type DatasetTablesArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  single?: InputMaybe<Scalars['Boolean']['input']>;
  where?: InputMaybe<Scalars['JSON']['input']>;
};

export type DatasetConnection = {
  __typename?: 'DatasetConnection';
  edges: Array<DatasetEdge>;
  pageInfo: PageInfo;
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type DatasetEdge = {
  __typename?: 'DatasetEdge';
  cursor: Scalars['String']['output'];
  node: Dataset;
};

/**
 * Dataset types
 *
 * * USER_MODEL: Contains user-defined models
 * * DATA_CONNECTION: Derived from a data connector to an external data source
 * * DATA_INGESTION: Derived from data ingestion pipelines
 */
export const DatasetType = {
  DataConnection: 'DATA_CONNECTION',
  DataIngestion: 'DATA_INGESTION',
  StaticModel: 'STATIC_MODEL',
  UserModel: 'USER_MODEL'
} as const;

export type DatasetType = typeof DatasetType[keyof typeof DatasetType];
export type DatasetTypeDefinition = DataConnectionDefinition | DataIngestionDefinition | DataModelDefinition | StaticModelDefinition;

export type FinishRunInput = {
  logsUrl: Scalars['String']['input'];
  metadata?: InputMaybe<UpdateMetadataInput>;
  runId: Scalars['ID']['input'];
  status: RunStatus;
  statusCode: Scalars['Int']['input'];
};

export type FinishRunPayload = {
  __typename?: 'FinishRunPayload';
  message?: Maybe<Scalars['String']['output']>;
  run?: Maybe<Run>;
  success: Scalars['Boolean']['output'];
};

export type FinishStepInput = {
  logsUrl: Scalars['String']['input'];
  status: StepStatus;
  stepId: Scalars['ID']['input'];
};

export type FinishStepPayload = {
  __typename?: 'FinishStepPayload';
  message?: Maybe<Scalars['String']['output']>;
  step?: Maybe<Step>;
  success: Scalars['Boolean']['output'];
};

export type Invitation = {
  __typename?: 'Invitation';
  acceptedAt?: Maybe<Scalars['DateTime']['output']>;
  acceptedBy?: Maybe<User>;
  createdAt: Scalars['DateTime']['output'];
  deletedAt?: Maybe<Scalars['DateTime']['output']>;
  email: Scalars['String']['output'];
  expiresAt: Scalars['DateTime']['output'];
  id: Scalars['ID']['output'];
  invitedBy: User;
  orgId: Scalars['ID']['output'];
  organization: Organization;
  status: InvitationStatus;
  userRole: MemberRole;
};

export type InvitationConnection = {
  __typename?: 'InvitationConnection';
  edges: Array<InvitationEdge>;
  pageInfo: PageInfo;
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type InvitationEdge = {
  __typename?: 'InvitationEdge';
  cursor: Scalars['String']['output'];
  node: Invitation;
};

/** Invitation status */
export const InvitationStatus = {
  Accepted: 'ACCEPTED',
  Expired: 'EXPIRED',
  Pending: 'PENDING',
  Revoked: 'REVOKED'
} as const;

export type InvitationStatus = typeof InvitationStatus[keyof typeof InvitationStatus];
/**
 * The materialization type represents the output of a run step that has
 * materialized data. For example, for a data model run, each materialization would
 * represent the output of a model execution. Each materialization is directly
 * associated with a table in the OSO data catalog.
 */
export type Materialization = {
  __typename?: 'Materialization';
  createdAt: Scalars['DateTime']['output'];
  datasetId: Scalars['ID']['output'];
  id: Scalars['ID']['output'];
  run: Run;
  runId: Scalars['ID']['output'];
  schema?: Maybe<Array<DataModelColumn>>;
  step: Step;
  stepId: Scalars['ID']['output'];
};

export type MaterializationConnection = {
  __typename?: 'MaterializationConnection';
  edges: Array<MaterializationEdge>;
  pageInfo: PageInfo;
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type MaterializationEdge = {
  __typename?: 'MaterializationEdge';
  cursor: Scalars['String']['output'];
  node: Materialization;
};

export const MemberRole = {
  Admin: 'admin',
  Owner: 'owner'
} as const;

export type MemberRole = typeof MemberRole[keyof typeof MemberRole];
export type ModelColumnContext = {
  __typename?: 'ModelColumnContext';
  context: Scalars['String']['output'];
  name: Scalars['String']['output'];
};

export type ModelColumnContextInput = {
  context: Scalars['String']['input'];
  name: Scalars['String']['input'];
};

export type ModelContext = {
  __typename?: 'ModelContext';
  columnContext?: Maybe<Array<ModelColumnContext>>;
  context?: Maybe<Scalars['String']['output']>;
  createdAt: Scalars['DateTime']['output'];
  datasetId: Scalars['ID']['output'];
  id: Scalars['ID']['output'];
  orgId: Scalars['ID']['output'];
  tableId: Scalars['String']['output'];
  updatedAt: Scalars['DateTime']['output'];
};

export type Mutation = {
  __typename?: 'Mutation';
  _empty?: Maybe<Scalars['String']['output']>;
  /** Accept an invitation */
  acceptInvitation: AcceptInvitationPayload;
  /** Add a user to organization */
  addUserByEmail: AddUserByEmailPayload;
  /** Cancel a run */
  cancelRun: CancelRunPayload;
  createDataConnection: CreateDataConnectionPayload;
  /**
   * System only. Create a dataset linked to a data connection schema
   * @system-only
   */
  createDataConnectionDatasets: SimplePayload;
  /** Request a run for a DATA_CONNECTION dataset */
  createDataConnectionRunRequest: CreateRunRequestPayload;
  createDataIngestionConfig: DataIngestion;
  /** Request a run for a DATA_INGEST dataset */
  createDataIngestionRunRequest: CreateRunRequestPayload;
  createDataModel: CreateDataModelPayload;
  createDataModelRelease: CreateDataModelReleasePayload;
  createDataModelRevision: CreateDataModelRevisionPayload;
  /** Create a new dataset */
  createDataset: CreateDatasetPayload;
  /** Create an invitation */
  createInvitation: CreateInvitationPayload;
  /**
   * System only. Create a materialization for a step
   * @system-only
   */
  createMaterialization: CreateMaterializationPayload;
  /** Create a new notebook */
  createNotebook: CreateNotebookPayload;
  createStaticModel: CreateStaticModelPayload;
  /** Request a run for a STATIC_MODEL */
  createStaticModelRunRequest: CreateRunRequestPayload;
  /**
   * Generate a pre-signed upload URL for the static model file. In order to upload
   * a static model, first create the static model using the `createStaticModel`
   * mutation, then call this mutation to get the upload URL. The file should be
   * uploaded to the returned URL using a POST. At this time only CSV files are
   * supported.
   */
  createStaticModelUploadUrl: Scalars['String']['output'];
  /** Request a run for a USER_MODEL dataset */
  createUserModelRunRequest: CreateRunRequestPayload;
  deleteDataConnection: SimplePayload;
  deleteDataModel: SimplePayload;
  /** Delete a dataset */
  deleteDataset: SimplePayload;
  deleteStaticModel: SimplePayload;
  /**
   * System only. Mark a run as finished.
   * @system-only
   */
  finishRun: FinishRunPayload;
  /**
   * System only. Mark a step as finished
   * @system-only
   */
  finishStep: FinishStepPayload;
  /** Publish the notebook HTML to the public */
  publishNotebook: PublishNotebookPayload;
  /** Remove a member from organization */
  removeMember: RemoveMemberPayload;
  /** Revoke an invitation */
  revokeInvitation: RevokeInvitationPayload;
  /** Save notebook preview image */
  saveNotebookPreview: SaveNotebookPreviewPayload;
  /**
   * System only. Save the generated published notebook HTML to object storage
   * @system-only
   */
  savePublishedNotebookHtml: SavePublishedNotebookHtmlPayload;
  /**
   * System only. Mark a run as started.
   * @system-only
   */
  startRun: StartRunPayload;
  /**
   * System only. Mark a step as started
   * @system-only
   */
  startStep: StartStepPayload;
  syncDataConnection: SyncDataConnectionPayload;
  /** Unpublish the notebook */
  unpublishNotebook: UnpublishNotebookPayload;
  updateDataModel: CreateDataModelPayload;
  /** Update a dataset */
  updateDataset: UpdateDatasetPayload;
  /** Update member role */
  updateMemberRole: UpdateMemberRolePayload;
  updateModelContext: UpdateModelContextPayload;
  /** Update a notebook */
  updateNotebook: UpdateNotebookPayload;
  /**
   * System only. Update run metadata. This can be called at any time
   * @system-only
   */
  updateRunMetadata: UpdateRunMetadataPayload;
  updateStaticModel: CreateStaticModelPayload;
};


export type MutationAcceptInvitationArgs = {
  input: AcceptInvitationInput;
};


export type MutationAddUserByEmailArgs = {
  input: AddUserByEmailInput;
};


export type MutationCancelRunArgs = {
  input: CancelRunInput;
};


export type MutationCreateDataConnectionArgs = {
  input: CreateDataConnectionInput;
};


export type MutationCreateDataConnectionDatasetsArgs = {
  input: CreateDataConnectionDatasetsInput;
};


export type MutationCreateDataConnectionRunRequestArgs = {
  input: CreateDataConnectionRunRequestInput;
};


export type MutationCreateDataIngestionConfigArgs = {
  input: CreateDataIngestionInput;
};


export type MutationCreateDataIngestionRunRequestArgs = {
  input: CreateDataIngestionRunRequestInput;
};


export type MutationCreateDataModelArgs = {
  input: CreateDataModelInput;
};


export type MutationCreateDataModelReleaseArgs = {
  input: CreateDataModelReleaseInput;
};


export type MutationCreateDataModelRevisionArgs = {
  input: CreateDataModelRevisionInput;
};


export type MutationCreateDatasetArgs = {
  input: CreateDatasetInput;
};


export type MutationCreateInvitationArgs = {
  input: CreateInvitationInput;
};


export type MutationCreateMaterializationArgs = {
  input: CreateMaterializationInput;
};


export type MutationCreateNotebookArgs = {
  input: CreateNotebookInput;
};


export type MutationCreateStaticModelArgs = {
  input: CreateStaticModelInput;
};


export type MutationCreateStaticModelRunRequestArgs = {
  input: CreateStaticModelRunRequestInput;
};


export type MutationCreateStaticModelUploadUrlArgs = {
  staticModelId: Scalars['ID']['input'];
};


export type MutationCreateUserModelRunRequestArgs = {
  input: CreateUserModelRunRequestInput;
};


export type MutationDeleteDataConnectionArgs = {
  id: Scalars['ID']['input'];
};


export type MutationDeleteDataModelArgs = {
  id: Scalars['ID']['input'];
};


export type MutationDeleteDatasetArgs = {
  id: Scalars['ID']['input'];
};


export type MutationDeleteStaticModelArgs = {
  id: Scalars['ID']['input'];
};


export type MutationFinishRunArgs = {
  input: FinishRunInput;
};


export type MutationFinishStepArgs = {
  input: FinishStepInput;
};


export type MutationPublishNotebookArgs = {
  notebookId: Scalars['ID']['input'];
};


export type MutationRemoveMemberArgs = {
  input: RemoveMemberInput;
};


export type MutationRevokeInvitationArgs = {
  input: RevokeInvitationInput;
};


export type MutationSaveNotebookPreviewArgs = {
  input: SaveNotebookPreviewInput;
};


export type MutationSavePublishedNotebookHtmlArgs = {
  input: SavePublishedNotebookHtmlInput;
};


export type MutationStartRunArgs = {
  input: StartRunInput;
};


export type MutationStartStepArgs = {
  input: StartStepInput;
};


export type MutationSyncDataConnectionArgs = {
  id: Scalars['ID']['input'];
};


export type MutationUnpublishNotebookArgs = {
  notebookId: Scalars['ID']['input'];
};


export type MutationUpdateDataModelArgs = {
  input: UpdateDataModelInput;
};


export type MutationUpdateDatasetArgs = {
  input: UpdateDatasetInput;
};


export type MutationUpdateMemberRoleArgs = {
  input: UpdateMemberRoleInput;
};


export type MutationUpdateModelContextArgs = {
  input: UpdateModelContextInput;
};


export type MutationUpdateNotebookArgs = {
  input: UpdateNotebookInput;
};


export type MutationUpdateRunMetadataArgs = {
  input: UpdateRunMetadataInput;
};


export type MutationUpdateStaticModelArgs = {
  input: UpdateStaticModelInput;
};

export type Notebook = {
  __typename?: 'Notebook';
  createdAt: Scalars['DateTime']['output'];
  creator: User;
  creatorId: Scalars['ID']['output'];
  data: Scalars['String']['output'];
  description?: Maybe<Scalars['String']['output']>;
  id: Scalars['ID']['output'];
  name: Scalars['String']['output'];
  orgId: Scalars['ID']['output'];
  organization: Organization;
  preview?: Maybe<Scalars['String']['output']>;
  updatedAt: Scalars['DateTime']['output'];
};

export type NotebookConnection = {
  __typename?: 'NotebookConnection';
  edges: Array<NotebookEdge>;
  pageInfo: PageInfo;
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type NotebookEdge = {
  __typename?: 'NotebookEdge';
  cursor: Scalars['String']['output'];
  node: Notebook;
};

export type Organization = {
  __typename?: 'Organization';
  createdAt: Scalars['DateTime']['output'];
  dataConnections: DataConnectionConnection;
  datasets: DatasetConnection;
  description?: Maybe<Scalars['String']['output']>;
  displayName?: Maybe<Scalars['String']['output']>;
  id: Scalars['ID']['output'];
  members: UserConnection;
  name: Scalars['String']['output'];
  notebooks: NotebookConnection;
  updatedAt: Scalars['DateTime']['output'];
};


export type OrganizationDataConnectionsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  single?: InputMaybe<Scalars['Boolean']['input']>;
  where?: InputMaybe<Scalars['JSON']['input']>;
};


export type OrganizationDatasetsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  single?: InputMaybe<Scalars['Boolean']['input']>;
  where?: InputMaybe<Scalars['JSON']['input']>;
};


export type OrganizationMembersArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  single?: InputMaybe<Scalars['Boolean']['input']>;
  where?: InputMaybe<Scalars['JSON']['input']>;
};


export type OrganizationNotebooksArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  single?: InputMaybe<Scalars['Boolean']['input']>;
  where?: InputMaybe<Scalars['JSON']['input']>;
};

export type OrganizationConnection = {
  __typename?: 'OrganizationConnection';
  edges: Array<OrganizationEdge>;
  pageInfo: PageInfo;
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type OrganizationEdge = {
  __typename?: 'OrganizationEdge';
  cursor: Scalars['String']['output'];
  node: Organization;
};

export type OrganizationMember = {
  __typename?: 'OrganizationMember';
  createdAt: Scalars['DateTime']['output'];
  id: Scalars['ID']['output'];
  orgId: Scalars['ID']['output'];
  user: User;
  userId: Scalars['ID']['output'];
  userRole: MemberRole;
};

/** Cursor-based pagination information */
export type PageInfo = {
  __typename?: 'PageInfo';
  endCursor?: Maybe<Scalars['String']['output']>;
  hasNextPage: Scalars['Boolean']['output'];
  hasPreviousPage: Scalars['Boolean']['output'];
  startCursor?: Maybe<Scalars['String']['output']>;
};

export type PreviewData = {
  __typename?: 'PreviewData';
  isAvailable: Scalars['Boolean']['output'];
  rows: Array<Scalars['JSON']['output']>;
};

export type PublishNotebookPayload = {
  __typename?: 'PublishNotebookPayload';
  message?: Maybe<Scalars['String']['output']>;
  run: Run;
  success: Scalars['Boolean']['output'];
};

export type Query = {
  __typename?: 'Query';
  _empty?: Maybe<Scalars['String']['output']>;
  /**
   * Query data connections with optional filtering and pagination.
   *
   * The where parameter accepts a JSON object with field-level filtering.
   * Each field can have comparison operators: eq, neq, gt, gte, lt, lte, in, like, ilike, is
   */
  dataConnections: DataConnectionConnection;
  /**
   * List all data models with optional filtering and pagination.
   *
   * The where parameter accepts a JSON object with field-level filtering.
   * Each field can have comparison operators: eq, neq, gt, gte, lt, lte, in, like, ilike, is
   *
   * Example:
   * ```json
   * {
   *   "name": { "like": "%user%" },
   *   "is_enabled": { "eq": true }
   * }
   * ```
   */
  dataModels: DataModelConnection;
  /**
   * List all datasets with optional filtering and pagination.
   *
   * The where parameter accepts a JSON object with field-level filtering.
   * Each field can have comparison operators: eq, neq, gt, gte, lt, lte, in, like, ilike, is
   *
   * Example:
   * ```json
   * {
   *   "name": { "like": "%hello%" },
   *   "type": { "eq": "USER_MODEL" }
   * }
   * ```
   */
  datasets: DatasetConnection;
  /**
   * List all invitations with optional filtering and pagination.
   *
   * The where parameter accepts a JSON object with field-level filtering.
   * Each field can have comparison operators: eq, neq, gt, gte, lt, lte, in, like, ilike, is
   *
   * Example:
   * ```json
   * {
   *   "status": { "eq": "PENDING" },
   *   "email": { "ilike": "%@example.com" }
   * }
   * ```
   */
  invitations: InvitationConnection;
  /**
   * Query notebooks with optional filtering and pagination.
   *
   * The where parameter accepts a JSON object with field-level filtering.
   * Each field can have comparison operators: eq, neq, gt, gte, lt, lte, in, like, ilike, is.
   *
   * Example:
   * ```json
   * {
   *   "notebook_name": { "like": "%churn%" },
   *   "created_at": { "gte": "2024-01-01T00:00:00Z" }
   * }
   * ```
   */
  notebooks: NotebookConnection;
  /**
   * Query organizations with optional filtering and pagination.
   *
   * The where parameter accepts a JSON object with field-level filtering.
   * Each field can have comparison operators: eq, neq, gt, gte, lt, lte, in, like, ilike, is
   *
   * Example:
   * ```json
   * {
   *   "name": { "like": "%oso%" },
   *   "created_at": { "gte": "2024-01-01T00:00:00Z" }
   * }
   * ```
   */
  organizations: OrganizationConnection;
  /**
   * List all runs with optional filtering and pagination.
   *
   * The where parameter accepts a JSON object with field-level filtering.
   * Each field can have comparison operators: eq, neq, gt, gte, lt, lte, in, like, ilike, is
   *
   * Example:
   * ```json
   * {
   *   "status": { "eq": "RUNNING" },
   *   "datasetId": { "eq": "dataset-uuid" }
   * }
   * ```
   */
  runs: RunConnection;
  staticModels: StaticModelConnection;
  /** System only. Access system level queries. */
  system: System;
  /** Get the currently authenticated user */
  viewer: Viewer;
};


export type QueryDataConnectionsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  single?: InputMaybe<Scalars['Boolean']['input']>;
  where?: InputMaybe<Scalars['JSON']['input']>;
};


export type QueryDataModelsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  single?: InputMaybe<Scalars['Boolean']['input']>;
  where?: InputMaybe<Scalars['JSON']['input']>;
};


export type QueryDatasetsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  single?: InputMaybe<Scalars['Boolean']['input']>;
  where?: InputMaybe<Scalars['JSON']['input']>;
};


export type QueryInvitationsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  single?: InputMaybe<Scalars['Boolean']['input']>;
  where?: InputMaybe<Scalars['JSON']['input']>;
};


export type QueryNotebooksArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  single?: InputMaybe<Scalars['Boolean']['input']>;
  where?: InputMaybe<Scalars['JSON']['input']>;
};


export type QueryOrganizationsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  single?: InputMaybe<Scalars['Boolean']['input']>;
  where?: InputMaybe<Scalars['JSON']['input']>;
};


export type QueryRunsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  single?: InputMaybe<Scalars['Boolean']['input']>;
  where?: InputMaybe<Scalars['JSON']['input']>;
};


export type QueryStaticModelsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  single?: InputMaybe<Scalars['Boolean']['input']>;
  where?: InputMaybe<Scalars['JSON']['input']>;
};

export type RemoveMemberInput = {
  orgId: Scalars['ID']['input'];
  userId: Scalars['ID']['input'];
};

export type RemoveMemberPayload = {
  __typename?: 'RemoveMemberPayload';
  message?: Maybe<Scalars['String']['output']>;
  success: Scalars['Boolean']['output'];
};

export type RevokeInvitationInput = {
  invitationId: Scalars['ID']['input'];
  orgId: Scalars['ID']['input'];
};

export type RevokeInvitationPayload = {
  __typename?: 'RevokeInvitationPayload';
  message?: Maybe<Scalars['String']['output']>;
  success: Scalars['Boolean']['output'];
};

export type Run = {
  __typename?: 'Run';
  dataset?: Maybe<Dataset>;
  datasetId?: Maybe<Scalars['ID']['output']>;
  finishedAt?: Maybe<Scalars['DateTime']['output']>;
  id: Scalars['ID']['output'];
  /**
   * The logs urls is returned as a presigned url to a cloud storage location. Use
   * a GET request on this URL to retrieve the logs for the run.
   */
  logsUrl?: Maybe<Scalars['String']['output']>;
  metadata?: Maybe<Scalars['JSON']['output']>;
  orgId: Scalars['ID']['output'];
  organization: Organization;
  queuedAt: Scalars['DateTime']['output'];
  requestedBy?: Maybe<User>;
  runType: RunType;
  startedAt?: Maybe<Scalars['DateTime']['output']>;
  status: RunStatus;
  steps: StepConnection;
  triggerType: RunTriggerType;
};

export type RunConnection = {
  __typename?: 'RunConnection';
  edges: Array<RunEdge>;
  pageInfo: PageInfo;
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type RunEdge = {
  __typename?: 'RunEdge';
  cursor: Scalars['String']['output'];
  node: Run;
};

export const RunStatus = {
  Canceled: 'CANCELED',
  Failed: 'FAILED',
  Queued: 'QUEUED',
  Running: 'RUNNING',
  Success: 'SUCCESS'
} as const;

export type RunStatus = typeof RunStatus[keyof typeof RunStatus];
/**
 * The scheduler schema defines types and queries related to scheduling data model
 * runs and ingest jobs.
 *
 * Runs are a generic representation of a data task that has been executed. So it's
 * meant to be quite flexible to accommodate different types of runs in the future.
 */
export const RunTriggerType = {
  Manual: 'MANUAL',
  Scheduled: 'SCHEDULED'
} as const;

export type RunTriggerType = typeof RunTriggerType[keyof typeof RunTriggerType];
export const RunType = {
  Manual: 'MANUAL',
  Scheduled: 'SCHEDULED'
} as const;

export type RunType = typeof RunType[keyof typeof RunType];
export type SaveNotebookPreviewInput = {
  notebookId: Scalars['ID']['input'];
  preview: Scalars['String']['input'];
};

export type SaveNotebookPreviewPayload = {
  __typename?: 'SaveNotebookPreviewPayload';
  message?: Maybe<Scalars['String']['output']>;
  notebook?: Maybe<Notebook>;
  previewUrl?: Maybe<Scalars['String']['output']>;
  success: Scalars['Boolean']['output'];
};

export type SavePublishedNotebookHtmlInput = {
  htmlContent: Scalars['String']['input'];
  notebookId: Scalars['ID']['input'];
};

export type SavePublishedNotebookHtmlPayload = {
  __typename?: 'SavePublishedNotebookHtmlPayload';
  message?: Maybe<Scalars['String']['output']>;
  success: Scalars['Boolean']['output'];
};

export type SimplePayload = {
  __typename?: 'SimplePayload';
  message?: Maybe<Scalars['String']['output']>;
  success: Scalars['Boolean']['output'];
};

export type StartRunInput = {
  runId: Scalars['ID']['input'];
};

export type StartRunPayload = {
  __typename?: 'StartRunPayload';
  message?: Maybe<Scalars['String']['output']>;
  run?: Maybe<Run>;
  success: Scalars['Boolean']['output'];
};

export type StartStepInput = {
  displayName: Scalars['String']['input'];
  name: Scalars['String']['input'];
  runId: Scalars['ID']['input'];
};

export type StartStepPayload = {
  __typename?: 'StartStepPayload';
  message?: Maybe<Scalars['String']['output']>;
  step: Step;
  success: Scalars['Boolean']['output'];
};

export type StaticModel = {
  __typename?: 'StaticModel';
  createdAt: Scalars['DateTime']['output'];
  dataset: Dataset;
  id: Scalars['ID']['output'];
  materializations: MaterializationConnection;
  modelContext?: Maybe<ModelContext>;
  name: Scalars['String']['output'];
  orgId: Scalars['ID']['output'];
  organization: Organization;
  previewData: PreviewData;
  runs: RunConnection;
  updatedAt: Scalars['DateTime']['output'];
};


export type StaticModelMaterializationsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  single?: InputMaybe<Scalars['Boolean']['input']>;
  where?: InputMaybe<Scalars['JSON']['input']>;
};


export type StaticModelRunsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
};

export type StaticModelConnection = {
  __typename?: 'StaticModelConnection';
  edges: Array<StaticModelEdge>;
  pageInfo: PageInfo;
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type StaticModelDefinition = {
  __typename?: 'StaticModelDefinition';
  datasetId: Scalars['ID']['output'];
  orgId: Scalars['ID']['output'];
  /**
   * If the dataset is of type STATIC_MODEL, this field will contain the list of static models
   * associated with the dataset. Otherwise it will be an empty list.
   */
  staticModels: StaticModelConnection;
};


export type StaticModelDefinitionStaticModelsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  single?: InputMaybe<Scalars['Boolean']['input']>;
  where?: InputMaybe<Scalars['JSON']['input']>;
};

export type StaticModelEdge = {
  __typename?: 'StaticModelEdge';
  cursor: Scalars['String']['output'];
  node: StaticModel;
};

export type Step = {
  __typename?: 'Step';
  displayName: Scalars['String']['output'];
  finishedAt?: Maybe<Scalars['DateTime']['output']>;
  id: Scalars['ID']['output'];
  logsUrl: Scalars['String']['output'];
  materializations: MaterializationConnection;
  name: Scalars['String']['output'];
  run: Run;
  runId: Scalars['ID']['output'];
  startedAt: Scalars['DateTime']['output'];
  status: StepStatus;
};

export type StepConnection = {
  __typename?: 'StepConnection';
  edges: Array<StepEdge>;
  pageInfo: PageInfo;
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type StepEdge = {
  __typename?: 'StepEdge';
  cursor: Scalars['String']['output'];
  node: Step;
};

export const StepStatus = {
  Canceled: 'CANCELED',
  Failed: 'FAILED',
  Running: 'RUNNING',
  Success: 'SUCCESS'
} as const;

export type StepStatus = typeof StepStatus[keyof typeof StepStatus];
export type SyncDataConnectionPayload = {
  __typename?: 'SyncDataConnectionPayload';
  message?: Maybe<Scalars['String']['output']>;
  run: Run;
  success: Scalars['Boolean']['output'];
};

export type System = {
  __typename?: 'System';
  /**
   * Resolve tables by their reference names to the actual table fqn in the data
   * warehouse. This is used by the query rewriter to batch resolve table
   * references as well as other internal operations.
   */
  resolveTables: Array<SystemResolvedTableReference>;
};


export type SystemResolveTablesArgs = {
  metadata?: InputMaybe<Scalars['JSON']['input']>;
  references: Array<Scalars['String']['input']>;
};

/**
 * Special type for system related reads that are only allowed by authenticated
 * service accounts that have system privileges.
 */
export type SystemResolvedTableReference = {
  __typename?: 'SystemResolvedTableReference';
  fqn: Scalars['String']['output'];
  reference: Scalars['String']['output'];
};

export type Table = {
  __typename?: 'Table';
  columns: Array<TableColumn>;
  dataset: Dataset;
  datasetId: Scalars['ID']['output'];
  id: Scalars['ID']['output'];
  name: Scalars['String']['output'];
  source: TableSource;
};

export type TableColumn = {
  __typename?: 'TableColumn';
  name: Scalars['String']['output'];
  nullable: Scalars['Boolean']['output'];
  type: Scalars['String']['output'];
};

export type TableConnection = {
  __typename?: 'TableConnection';
  edges: Array<TableEdge>;
  pageInfo: PageInfo;
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type TableEdge = {
  __typename?: 'TableEdge';
  cursor: Scalars['String']['output'];
  node: Table;
};

export type TableSource = DataConnection | DataIngestion | DataModel | StaticModel;

export type UnpublishNotebookPayload = {
  __typename?: 'UnpublishNotebookPayload';
  message?: Maybe<Scalars['String']['output']>;
  success: Scalars['Boolean']['output'];
};

export type UpdateDataModelInput = {
  dataModelId: Scalars['ID']['input'];
  isEnabled?: InputMaybe<Scalars['Boolean']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
};

export type UpdateDatasetInput = {
  description?: InputMaybe<Scalars['String']['input']>;
  displayName?: InputMaybe<Scalars['String']['input']>;
  id: Scalars['ID']['input'];
  name?: InputMaybe<Scalars['String']['input']>;
};

export type UpdateDatasetPayload = {
  __typename?: 'UpdateDatasetPayload';
  dataset?: Maybe<Dataset>;
  message?: Maybe<Scalars['String']['output']>;
  success: Scalars['Boolean']['output'];
};

export type UpdateMemberRoleInput = {
  orgId: Scalars['ID']['input'];
  role: MemberRole;
  userId: Scalars['ID']['input'];
};

export type UpdateMemberRolePayload = {
  __typename?: 'UpdateMemberRolePayload';
  member?: Maybe<OrganizationMember>;
  message?: Maybe<Scalars['String']['output']>;
  success: Scalars['Boolean']['output'];
};

export type UpdateMetadataInput = {
  merge?: InputMaybe<Scalars['Boolean']['input']>;
  value: Scalars['JSON']['input'];
};

export type UpdateModelContextInput = {
  columnContext?: InputMaybe<Array<ModelColumnContextInput>>;
  context?: InputMaybe<Scalars['String']['input']>;
  datasetId: Scalars['ID']['input'];
  modelId: Scalars['String']['input'];
};

export type UpdateModelContextPayload = {
  __typename?: 'UpdateModelContextPayload';
  message?: Maybe<Scalars['String']['output']>;
  modelContext?: Maybe<ModelContext>;
  success: Scalars['Boolean']['output'];
};

export type UpdateNotebookInput = {
  description?: InputMaybe<Scalars['String']['input']>;
  id: Scalars['ID']['input'];
  name?: InputMaybe<Scalars['String']['input']>;
};

export type UpdateNotebookPayload = {
  __typename?: 'UpdateNotebookPayload';
  message?: Maybe<Scalars['String']['output']>;
  notebook?: Maybe<Notebook>;
  success: Scalars['Boolean']['output'];
};

export type UpdateRunMetadataInput = {
  metadata: UpdateMetadataInput;
  runId: Scalars['ID']['input'];
};

export type UpdateRunMetadataPayload = {
  __typename?: 'UpdateRunMetadataPayload';
  message?: Maybe<Scalars['String']['output']>;
  run?: Maybe<Run>;
  success: Scalars['Boolean']['output'];
};

export type UpdateStaticModelInput = {
  name?: InputMaybe<Scalars['String']['input']>;
  staticModelId: Scalars['ID']['input'];
};

export type User = {
  __typename?: 'User';
  avatarUrl?: Maybe<Scalars['String']['output']>;
  email: Scalars['String']['output'];
  fullName?: Maybe<Scalars['String']['output']>;
  id: Scalars['ID']['output'];
  organizations: OrganizationConnection;
};


export type UserOrganizationsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  single?: InputMaybe<Scalars['Boolean']['input']>;
  where?: InputMaybe<Scalars['JSON']['input']>;
};

export type UserConnection = {
  __typename?: 'UserConnection';
  edges: Array<UserEdge>;
  pageInfo: PageInfo;
  totalCount?: Maybe<Scalars['Int']['output']>;
};

export type UserEdge = {
  __typename?: 'UserEdge';
  cursor: Scalars['String']['output'];
  node: User;
};

/** Currently authenticated user */
export type Viewer = {
  __typename?: 'Viewer';
  avatarUrl?: Maybe<Scalars['String']['output']>;
  datasets: DatasetConnection;
  email: Scalars['String']['output'];
  fullName?: Maybe<Scalars['String']['output']>;
  id: Scalars['ID']['output'];
  invitations: InvitationConnection;
  notebooks: NotebookConnection;
  organizations: OrganizationConnection;
  runs: RunConnection;
};


/** Currently authenticated user */
export type ViewerDatasetsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  single?: InputMaybe<Scalars['Boolean']['input']>;
  where?: InputMaybe<Scalars['JSON']['input']>;
};


/** Currently authenticated user */
export type ViewerInvitationsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  single?: InputMaybe<Scalars['Boolean']['input']>;
  where?: InputMaybe<Scalars['JSON']['input']>;
};


/** Currently authenticated user */
export type ViewerNotebooksArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  single?: InputMaybe<Scalars['Boolean']['input']>;
  where?: InputMaybe<Scalars['JSON']['input']>;
};


/** Currently authenticated user */
export type ViewerOrganizationsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  single?: InputMaybe<Scalars['Boolean']['input']>;
  where?: InputMaybe<Scalars['JSON']['input']>;
};


/** Currently authenticated user */
export type ViewerRunsArgs = {
  after?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  single?: InputMaybe<Scalars['Boolean']['input']>;
  where?: InputMaybe<Scalars['JSON']['input']>;
};



export type ResolverTypeWrapper<T> = Promise<T> | T;


export type ResolverWithResolve<TResult, TParent, TContext, TArgs> = {
  resolve: ResolverFn<TResult, TParent, TContext, TArgs>;
};
export type Resolver<TResult, TParent = Record<PropertyKey, never>, TContext = Record<PropertyKey, never>, TArgs = Record<PropertyKey, never>> = ResolverFn<TResult, TParent, TContext, TArgs> | ResolverWithResolve<TResult, TParent, TContext, TArgs>;

export type ResolverFn<TResult, TParent, TContext, TArgs> = (
  parent: TParent,
  args: TArgs,
  context: TContext,
  info: GraphQLResolveInfo
) => Promise<TResult> | TResult;

export type SubscriptionSubscribeFn<TResult, TParent, TContext, TArgs> = (
  parent: TParent,
  args: TArgs,
  context: TContext,
  info: GraphQLResolveInfo
) => AsyncIterable<TResult> | Promise<AsyncIterable<TResult>>;

export type SubscriptionResolveFn<TResult, TParent, TContext, TArgs> = (
  parent: TParent,
  args: TArgs,
  context: TContext,
  info: GraphQLResolveInfo
) => TResult | Promise<TResult>;

export interface SubscriptionSubscriberObject<TResult, TKey extends string, TParent, TContext, TArgs> {
  subscribe: SubscriptionSubscribeFn<{ [key in TKey]: TResult }, TParent, TContext, TArgs>;
  resolve?: SubscriptionResolveFn<TResult, { [key in TKey]: TResult }, TContext, TArgs>;
}

export interface SubscriptionResolverObject<TResult, TParent, TContext, TArgs> {
  subscribe: SubscriptionSubscribeFn<any, TParent, TContext, TArgs>;
  resolve: SubscriptionResolveFn<TResult, any, TContext, TArgs>;
}

export type SubscriptionObject<TResult, TKey extends string, TParent, TContext, TArgs> =
  | SubscriptionSubscriberObject<TResult, TKey, TParent, TContext, TArgs>
  | SubscriptionResolverObject<TResult, TParent, TContext, TArgs>;

export type SubscriptionResolver<TResult, TKey extends string, TParent = Record<PropertyKey, never>, TContext = Record<PropertyKey, never>, TArgs = Record<PropertyKey, never>> =
  | ((...args: any[]) => SubscriptionObject<TResult, TKey, TParent, TContext, TArgs>)
  | SubscriptionObject<TResult, TKey, TParent, TContext, TArgs>;

export type TypeResolveFn<TTypes, TParent = Record<PropertyKey, never>, TContext = Record<PropertyKey, never>> = (
  parent: TParent,
  context: TContext,
  info: GraphQLResolveInfo
) => Maybe<TTypes> | Promise<Maybe<TTypes>>;

export type IsTypeOfResolverFn<T = Record<PropertyKey, never>, TContext = Record<PropertyKey, never>> = (obj: T, context: TContext, info: GraphQLResolveInfo) => boolean | Promise<boolean>;

export type NextResolverFn<T> = () => Promise<T>;

export type DirectiveResolverFn<TResult = Record<PropertyKey, never>, TParent = Record<PropertyKey, never>, TContext = Record<PropertyKey, never>, TArgs = Record<PropertyKey, never>> = (
  next: NextResolverFn<TResult>,
  parent: TParent,
  args: TArgs,
  context: TContext,
  info: GraphQLResolveInfo
) => TResult | Promise<TResult>;



/** Mapping of union types */
export type ResolversUnionTypes<_RefType extends Record<string, unknown>> = {
  DatasetTypeDefinition:
    | ( Omit<DataConnectionDefinition, 'dataConnectionAlias'> & { dataConnectionAlias: _RefType['DataConnectionAlias'] } )
    | ( Omit<DataIngestionDefinition, 'dataIngestion'> & { dataIngestion?: Maybe<_RefType['DataIngestion']> } )
    | ( Omit<DataModelDefinition, 'dataModels'> & { dataModels: _RefType['DataModelConnection'] } )
    | ( Omit<StaticModelDefinition, 'staticModels'> & { staticModels: _RefType['StaticModelConnection'] } )
  ;
  TableSource:
    | ( DataConnectionAliasRow )
    | ( DataIngestionsRow )
    | ( ModelRow )
    | ( StaticModelRow )
  ;
};


/** Mapping between all available schema types and the resolvers types */
export type ResolversTypes = {
  AcceptInvitationInput: AcceptInvitationInput;
  AcceptInvitationPayload: ResolverTypeWrapper<Omit<AcceptInvitationPayload, 'member'> & { member?: Maybe<ResolversTypes['OrganizationMember']> }>;
  AddUserByEmailInput: AddUserByEmailInput;
  AddUserByEmailPayload: ResolverTypeWrapper<Omit<AddUserByEmailPayload, 'member'> & { member?: Maybe<ResolversTypes['OrganizationMember']> }>;
  Boolean: ResolverTypeWrapper<Scalars['Boolean']['output']>;
  CancelRunInput: CancelRunInput;
  CancelRunPayload: ResolverTypeWrapper<Omit<CancelRunPayload, 'run'> & { run?: Maybe<ResolversTypes['Run']> }>;
  CreateDataConnectionDatasetsInput: CreateDataConnectionDatasetsInput;
  CreateDataConnectionInput: CreateDataConnectionInput;
  CreateDataConnectionPayload: ResolverTypeWrapper<Omit<CreateDataConnectionPayload, 'dataConnection'> & { dataConnection?: Maybe<ResolversTypes['DataConnection']> }>;
  CreateDataConnectionRunRequestInput: CreateDataConnectionRunRequestInput;
  CreateDataIngestionInput: CreateDataIngestionInput;
  CreateDataIngestionRunRequestInput: CreateDataIngestionRunRequestInput;
  CreateDataModelInput: CreateDataModelInput;
  CreateDataModelPayload: ResolverTypeWrapper<Omit<CreateDataModelPayload, 'dataModel'> & { dataModel?: Maybe<ResolversTypes['DataModel']> }>;
  CreateDataModelReleaseInput: CreateDataModelReleaseInput;
  CreateDataModelReleasePayload: ResolverTypeWrapper<Omit<CreateDataModelReleasePayload, 'dataModelRelease'> & { dataModelRelease?: Maybe<ResolversTypes['DataModelRelease']> }>;
  CreateDataModelRevisionInput: CreateDataModelRevisionInput;
  CreateDataModelRevisionPayload: ResolverTypeWrapper<Omit<CreateDataModelRevisionPayload, 'dataModelRevision'> & { dataModelRevision?: Maybe<ResolversTypes['DataModelRevision']> }>;
  CreateDatasetInput: CreateDatasetInput;
  CreateDatasetPayload: ResolverTypeWrapper<Omit<CreateDatasetPayload, 'dataset'> & { dataset?: Maybe<ResolversTypes['Dataset']> }>;
  CreateInvitationInput: CreateInvitationInput;
  CreateInvitationPayload: ResolverTypeWrapper<Omit<CreateInvitationPayload, 'invitation'> & { invitation?: Maybe<ResolversTypes['Invitation']> }>;
  CreateMaterializationInput: CreateMaterializationInput;
  CreateMaterializationPayload: ResolverTypeWrapper<Omit<CreateMaterializationPayload, 'materialization'> & { materialization: ResolversTypes['Materialization'] }>;
  CreateNotebookInput: CreateNotebookInput;
  CreateNotebookPayload: ResolverTypeWrapper<Omit<CreateNotebookPayload, 'notebook'> & { notebook?: Maybe<ResolversTypes['Notebook']> }>;
  CreateRunRequestPayload: ResolverTypeWrapper<Omit<CreateRunRequestPayload, 'run'> & { run: ResolversTypes['Run'] }>;
  CreateStaticModelInput: CreateStaticModelInput;
  CreateStaticModelPayload: ResolverTypeWrapper<Omit<CreateStaticModelPayload, 'staticModel'> & { staticModel?: Maybe<ResolversTypes['StaticModel']> }>;
  CreateStaticModelRunRequestInput: CreateStaticModelRunRequestInput;
  CreateUserModelRunRequestInput: CreateUserModelRunRequestInput;
  DataConnection: ResolverTypeWrapper<DataConnectionAliasRow>;
  DataConnectionAlias: ResolverTypeWrapper<Omit<DataConnectionAlias, 'materializations' | 'modelContext'> & { materializations: ResolversTypes['MaterializationConnection'], modelContext?: Maybe<ResolversTypes['ModelContext']> }>;
  DataConnectionConnection: ResolverTypeWrapper<Omit<DataConnectionConnection, 'edges'> & { edges: Array<ResolversTypes['DataConnectionEdge']> }>;
  DataConnectionDefinition: ResolverTypeWrapper<Omit<DataConnectionDefinition, 'dataConnectionAlias'> & { dataConnectionAlias: ResolversTypes['DataConnectionAlias'] }>;
  DataConnectionEdge: ResolverTypeWrapper<Omit<DataConnectionEdge, 'node'> & { node: ResolversTypes['DataConnection'] }>;
  DataConnectionSchema: ResolverTypeWrapper<DataConnectionSchema>;
  DataConnectionSchemaInput: DataConnectionSchemaInput;
  DataConnectionTable: ResolverTypeWrapper<DataConnectionTable>;
  DataConnectionTableInput: DataConnectionTableInput;
  DataConnectionType: DataConnectionType;
  DataIngestion: ResolverTypeWrapper<DataIngestionsRow>;
  DataIngestionConnection: ResolverTypeWrapper<Omit<DataIngestionConnection, 'edges'> & { edges: Array<ResolversTypes['DataIngestionEdge']> }>;
  DataIngestionDefinition: ResolverTypeWrapper<Omit<DataIngestionDefinition, 'dataIngestion'> & { dataIngestion?: Maybe<ResolversTypes['DataIngestion']> }>;
  DataIngestionEdge: ResolverTypeWrapper<Omit<DataIngestionEdge, 'node'> & { node: ResolversTypes['DataIngestion'] }>;
  DataIngestionFactoryType: DataIngestionFactoryType;
  DataModel: ResolverTypeWrapper<ModelRow>;
  DataModelColumn: ResolverTypeWrapper<DataModelColumn>;
  DataModelColumnInput: DataModelColumnInput;
  DataModelConnection: ResolverTypeWrapper<Omit<DataModelConnection, 'edges'> & { edges: Array<ResolversTypes['DataModelEdge']> }>;
  DataModelDefinition: ResolverTypeWrapper<Omit<DataModelDefinition, 'dataModels'> & { dataModels: ResolversTypes['DataModelConnection'] }>;
  DataModelDependency: ResolverTypeWrapper<DataModelDependency>;
  DataModelDependencyInput: DataModelDependencyInput;
  DataModelEdge: ResolverTypeWrapper<Omit<DataModelEdge, 'node'> & { node: ResolversTypes['DataModel'] }>;
  DataModelKind: DataModelKind;
  DataModelKindOptions: ResolverTypeWrapper<DataModelKindOptions>;
  DataModelKindOptionsInput: DataModelKindOptionsInput;
  DataModelRelease: ResolverTypeWrapper<ModelReleaseRow>;
  DataModelReleaseConnection: ResolverTypeWrapper<Omit<DataModelReleaseConnection, 'edges'> & { edges: Array<ResolversTypes['DataModelReleaseEdge']> }>;
  DataModelReleaseEdge: ResolverTypeWrapper<Omit<DataModelReleaseEdge, 'node'> & { node: ResolversTypes['DataModelRelease'] }>;
  DataModelRevision: ResolverTypeWrapper<ModelRevisionRow>;
  DataModelRevisionConnection: ResolverTypeWrapper<Omit<DataModelRevisionConnection, 'edges'> & { edges: Array<ResolversTypes['DataModelRevisionEdge']> }>;
  DataModelRevisionEdge: ResolverTypeWrapper<Omit<DataModelRevisionEdge, 'node'> & { node: ResolversTypes['DataModelRevision'] }>;
  Dataset: ResolverTypeWrapper<DatasetsRow>;
  DatasetConnection: ResolverTypeWrapper<Omit<DatasetConnection, 'edges'> & { edges: Array<ResolversTypes['DatasetEdge']> }>;
  DatasetEdge: ResolverTypeWrapper<Omit<DatasetEdge, 'node'> & { node: ResolversTypes['Dataset'] }>;
  DatasetType: DatasetType;
  DatasetTypeDefinition: ResolverTypeWrapper<ResolversUnionTypes<ResolversTypes>['DatasetTypeDefinition']>;
  DateTime: ResolverTypeWrapper<Scalars['DateTime']['output']>;
  FinishRunInput: FinishRunInput;
  FinishRunPayload: ResolverTypeWrapper<Omit<FinishRunPayload, 'run'> & { run?: Maybe<ResolversTypes['Run']> }>;
  FinishStepInput: FinishStepInput;
  FinishStepPayload: ResolverTypeWrapper<Omit<FinishStepPayload, 'step'> & { step?: Maybe<ResolversTypes['Step']> }>;
  ID: ResolverTypeWrapper<Scalars['ID']['output']>;
  Int: ResolverTypeWrapper<Scalars['Int']['output']>;
  Invitation: ResolverTypeWrapper<InvitationsRow>;
  InvitationConnection: ResolverTypeWrapper<Omit<InvitationConnection, 'edges'> & { edges: Array<ResolversTypes['InvitationEdge']> }>;
  InvitationEdge: ResolverTypeWrapper<Omit<InvitationEdge, 'node'> & { node: ResolversTypes['Invitation'] }>;
  InvitationStatus: InvitationStatus;
  JSON: ResolverTypeWrapper<Scalars['JSON']['output']>;
  Materialization: ResolverTypeWrapper<MaterializationRow>;
  MaterializationConnection: ResolverTypeWrapper<Omit<MaterializationConnection, 'edges'> & { edges: Array<ResolversTypes['MaterializationEdge']> }>;
  MaterializationEdge: ResolverTypeWrapper<Omit<MaterializationEdge, 'node'> & { node: ResolversTypes['Materialization'] }>;
  MemberRole: MemberRole;
  ModelColumnContext: ResolverTypeWrapper<ModelColumnContext>;
  ModelColumnContextInput: ModelColumnContextInput;
  ModelContext: ResolverTypeWrapper<ModelContextsRow>;
  Mutation: ResolverTypeWrapper<Record<PropertyKey, never>>;
  Notebook: ResolverTypeWrapper<NotebooksRow>;
  NotebookConnection: ResolverTypeWrapper<Omit<NotebookConnection, 'edges'> & { edges: Array<ResolversTypes['NotebookEdge']> }>;
  NotebookEdge: ResolverTypeWrapper<Omit<NotebookEdge, 'node'> & { node: ResolversTypes['Notebook'] }>;
  Organization: ResolverTypeWrapper<OrganizationsRow>;
  OrganizationConnection: ResolverTypeWrapper<Omit<OrganizationConnection, 'edges'> & { edges: Array<ResolversTypes['OrganizationEdge']> }>;
  OrganizationEdge: ResolverTypeWrapper<Omit<OrganizationEdge, 'node'> & { node: ResolversTypes['Organization'] }>;
  OrganizationMember: ResolverTypeWrapper<Omit<OrganizationMember, 'user'> & { user: ResolversTypes['User'] }>;
  PageInfo: ResolverTypeWrapper<PageInfo>;
  PreviewData: ResolverTypeWrapper<PreviewData>;
  PublishNotebookPayload: ResolverTypeWrapper<Omit<PublishNotebookPayload, 'run'> & { run: ResolversTypes['Run'] }>;
  Query: ResolverTypeWrapper<Record<PropertyKey, never>>;
  RemoveMemberInput: RemoveMemberInput;
  RemoveMemberPayload: ResolverTypeWrapper<RemoveMemberPayload>;
  RevokeInvitationInput: RevokeInvitationInput;
  RevokeInvitationPayload: ResolverTypeWrapper<RevokeInvitationPayload>;
  Run: ResolverTypeWrapper<RunRow>;
  RunConnection: ResolverTypeWrapper<Omit<RunConnection, 'edges'> & { edges: Array<ResolversTypes['RunEdge']> }>;
  RunEdge: ResolverTypeWrapper<Omit<RunEdge, 'node'> & { node: ResolversTypes['Run'] }>;
  RunStatus: RunStatus;
  RunTriggerType: RunTriggerType;
  RunType: RunType;
  SaveNotebookPreviewInput: SaveNotebookPreviewInput;
  SaveNotebookPreviewPayload: ResolverTypeWrapper<Omit<SaveNotebookPreviewPayload, 'notebook'> & { notebook?: Maybe<ResolversTypes['Notebook']> }>;
  SavePublishedNotebookHtmlInput: SavePublishedNotebookHtmlInput;
  SavePublishedNotebookHtmlPayload: ResolverTypeWrapper<SavePublishedNotebookHtmlPayload>;
  SimplePayload: ResolverTypeWrapper<SimplePayload>;
  StartRunInput: StartRunInput;
  StartRunPayload: ResolverTypeWrapper<Omit<StartRunPayload, 'run'> & { run?: Maybe<ResolversTypes['Run']> }>;
  StartStepInput: StartStepInput;
  StartStepPayload: ResolverTypeWrapper<Omit<StartStepPayload, 'step'> & { step: ResolversTypes['Step'] }>;
  StaticModel: ResolverTypeWrapper<StaticModelRow>;
  StaticModelConnection: ResolverTypeWrapper<Omit<StaticModelConnection, 'edges'> & { edges: Array<ResolversTypes['StaticModelEdge']> }>;
  StaticModelDefinition: ResolverTypeWrapper<Omit<StaticModelDefinition, 'staticModels'> & { staticModels: ResolversTypes['StaticModelConnection'] }>;
  StaticModelEdge: ResolverTypeWrapper<Omit<StaticModelEdge, 'node'> & { node: ResolversTypes['StaticModel'] }>;
  Step: ResolverTypeWrapper<StepRow>;
  StepConnection: ResolverTypeWrapper<Omit<StepConnection, 'edges'> & { edges: Array<ResolversTypes['StepEdge']> }>;
  StepEdge: ResolverTypeWrapper<Omit<StepEdge, 'node'> & { node: ResolversTypes['Step'] }>;
  StepStatus: StepStatus;
  String: ResolverTypeWrapper<Scalars['String']['output']>;
  SyncDataConnectionPayload: ResolverTypeWrapper<Omit<SyncDataConnectionPayload, 'run'> & { run: ResolversTypes['Run'] }>;
  System: ResolverTypeWrapper<System>;
  SystemResolvedTableReference: ResolverTypeWrapper<SystemResolvedTableReference>;
  Table: ResolverTypeWrapper<Omit<Table, 'columns' | 'dataset' | 'source'> & { columns: Array<ResolversTypes['TableColumn']>, dataset: ResolversTypes['Dataset'], source: ResolversTypes['TableSource'] }>;
  TableColumn: ResolverTypeWrapper<TableColumn>;
  TableConnection: ResolverTypeWrapper<Omit<TableConnection, 'edges'> & { edges: Array<ResolversTypes['TableEdge']> }>;
  TableEdge: ResolverTypeWrapper<Omit<TableEdge, 'node'> & { node: ResolversTypes['Table'] }>;
  TableSource: ResolverTypeWrapper<ResolversUnionTypes<ResolversTypes>['TableSource']>;
  UnpublishNotebookPayload: ResolverTypeWrapper<UnpublishNotebookPayload>;
  UpdateDataModelInput: UpdateDataModelInput;
  UpdateDatasetInput: UpdateDatasetInput;
  UpdateDatasetPayload: ResolverTypeWrapper<Omit<UpdateDatasetPayload, 'dataset'> & { dataset?: Maybe<ResolversTypes['Dataset']> }>;
  UpdateMemberRoleInput: UpdateMemberRoleInput;
  UpdateMemberRolePayload: ResolverTypeWrapper<Omit<UpdateMemberRolePayload, 'member'> & { member?: Maybe<ResolversTypes['OrganizationMember']> }>;
  UpdateMetadataInput: UpdateMetadataInput;
  UpdateModelContextInput: UpdateModelContextInput;
  UpdateModelContextPayload: ResolverTypeWrapper<Omit<UpdateModelContextPayload, 'modelContext'> & { modelContext?: Maybe<ResolversTypes['ModelContext']> }>;
  UpdateNotebookInput: UpdateNotebookInput;
  UpdateNotebookPayload: ResolverTypeWrapper<Omit<UpdateNotebookPayload, 'notebook'> & { notebook?: Maybe<ResolversTypes['Notebook']> }>;
  UpdateRunMetadataInput: UpdateRunMetadataInput;
  UpdateRunMetadataPayload: ResolverTypeWrapper<Omit<UpdateRunMetadataPayload, 'run'> & { run?: Maybe<ResolversTypes['Run']> }>;
  UpdateStaticModelInput: UpdateStaticModelInput;
  User: ResolverTypeWrapper<UserProfilesRow>;
  UserConnection: ResolverTypeWrapper<Omit<UserConnection, 'edges'> & { edges: Array<ResolversTypes['UserEdge']> }>;
  UserEdge: ResolverTypeWrapper<Omit<UserEdge, 'node'> & { node: ResolversTypes['User'] }>;
  Viewer: ResolverTypeWrapper<Omit<Viewer, 'datasets' | 'invitations' | 'notebooks' | 'organizations' | 'runs'> & { datasets: ResolversTypes['DatasetConnection'], invitations: ResolversTypes['InvitationConnection'], notebooks: ResolversTypes['NotebookConnection'], organizations: ResolversTypes['OrganizationConnection'], runs: ResolversTypes['RunConnection'] }>;
};

/** Mapping between all available schema types and the resolvers parents */
export type ResolversParentTypes = {
  AcceptInvitationInput: AcceptInvitationInput;
  AcceptInvitationPayload: Omit<AcceptInvitationPayload, 'member'> & { member?: Maybe<ResolversParentTypes['OrganizationMember']> };
  AddUserByEmailInput: AddUserByEmailInput;
  AddUserByEmailPayload: Omit<AddUserByEmailPayload, 'member'> & { member?: Maybe<ResolversParentTypes['OrganizationMember']> };
  Boolean: Scalars['Boolean']['output'];
  CancelRunInput: CancelRunInput;
  CancelRunPayload: Omit<CancelRunPayload, 'run'> & { run?: Maybe<ResolversParentTypes['Run']> };
  CreateDataConnectionDatasetsInput: CreateDataConnectionDatasetsInput;
  CreateDataConnectionInput: CreateDataConnectionInput;
  CreateDataConnectionPayload: Omit<CreateDataConnectionPayload, 'dataConnection'> & { dataConnection?: Maybe<ResolversParentTypes['DataConnection']> };
  CreateDataConnectionRunRequestInput: CreateDataConnectionRunRequestInput;
  CreateDataIngestionInput: CreateDataIngestionInput;
  CreateDataIngestionRunRequestInput: CreateDataIngestionRunRequestInput;
  CreateDataModelInput: CreateDataModelInput;
  CreateDataModelPayload: Omit<CreateDataModelPayload, 'dataModel'> & { dataModel?: Maybe<ResolversParentTypes['DataModel']> };
  CreateDataModelReleaseInput: CreateDataModelReleaseInput;
  CreateDataModelReleasePayload: Omit<CreateDataModelReleasePayload, 'dataModelRelease'> & { dataModelRelease?: Maybe<ResolversParentTypes['DataModelRelease']> };
  CreateDataModelRevisionInput: CreateDataModelRevisionInput;
  CreateDataModelRevisionPayload: Omit<CreateDataModelRevisionPayload, 'dataModelRevision'> & { dataModelRevision?: Maybe<ResolversParentTypes['DataModelRevision']> };
  CreateDatasetInput: CreateDatasetInput;
  CreateDatasetPayload: Omit<CreateDatasetPayload, 'dataset'> & { dataset?: Maybe<ResolversParentTypes['Dataset']> };
  CreateInvitationInput: CreateInvitationInput;
  CreateInvitationPayload: Omit<CreateInvitationPayload, 'invitation'> & { invitation?: Maybe<ResolversParentTypes['Invitation']> };
  CreateMaterializationInput: CreateMaterializationInput;
  CreateMaterializationPayload: Omit<CreateMaterializationPayload, 'materialization'> & { materialization: ResolversParentTypes['Materialization'] };
  CreateNotebookInput: CreateNotebookInput;
  CreateNotebookPayload: Omit<CreateNotebookPayload, 'notebook'> & { notebook?: Maybe<ResolversParentTypes['Notebook']> };
  CreateRunRequestPayload: Omit<CreateRunRequestPayload, 'run'> & { run: ResolversParentTypes['Run'] };
  CreateStaticModelInput: CreateStaticModelInput;
  CreateStaticModelPayload: Omit<CreateStaticModelPayload, 'staticModel'> & { staticModel?: Maybe<ResolversParentTypes['StaticModel']> };
  CreateStaticModelRunRequestInput: CreateStaticModelRunRequestInput;
  CreateUserModelRunRequestInput: CreateUserModelRunRequestInput;
  DataConnection: DataConnectionAliasRow;
  DataConnectionAlias: Omit<DataConnectionAlias, 'materializations' | 'modelContext'> & { materializations: ResolversParentTypes['MaterializationConnection'], modelContext?: Maybe<ResolversParentTypes['ModelContext']> };
  DataConnectionConnection: Omit<DataConnectionConnection, 'edges'> & { edges: Array<ResolversParentTypes['DataConnectionEdge']> };
  DataConnectionDefinition: Omit<DataConnectionDefinition, 'dataConnectionAlias'> & { dataConnectionAlias: ResolversParentTypes['DataConnectionAlias'] };
  DataConnectionEdge: Omit<DataConnectionEdge, 'node'> & { node: ResolversParentTypes['DataConnection'] };
  DataConnectionSchema: DataConnectionSchema;
  DataConnectionSchemaInput: DataConnectionSchemaInput;
  DataConnectionTable: DataConnectionTable;
  DataConnectionTableInput: DataConnectionTableInput;
  DataIngestion: DataIngestionsRow;
  DataIngestionConnection: Omit<DataIngestionConnection, 'edges'> & { edges: Array<ResolversParentTypes['DataIngestionEdge']> };
  DataIngestionDefinition: Omit<DataIngestionDefinition, 'dataIngestion'> & { dataIngestion?: Maybe<ResolversParentTypes['DataIngestion']> };
  DataIngestionEdge: Omit<DataIngestionEdge, 'node'> & { node: ResolversParentTypes['DataIngestion'] };
  DataModel: ModelRow;
  DataModelColumn: DataModelColumn;
  DataModelColumnInput: DataModelColumnInput;
  DataModelConnection: Omit<DataModelConnection, 'edges'> & { edges: Array<ResolversParentTypes['DataModelEdge']> };
  DataModelDefinition: Omit<DataModelDefinition, 'dataModels'> & { dataModels: ResolversParentTypes['DataModelConnection'] };
  DataModelDependency: DataModelDependency;
  DataModelDependencyInput: DataModelDependencyInput;
  DataModelEdge: Omit<DataModelEdge, 'node'> & { node: ResolversParentTypes['DataModel'] };
  DataModelKindOptions: DataModelKindOptions;
  DataModelKindOptionsInput: DataModelKindOptionsInput;
  DataModelRelease: ModelReleaseRow;
  DataModelReleaseConnection: Omit<DataModelReleaseConnection, 'edges'> & { edges: Array<ResolversParentTypes['DataModelReleaseEdge']> };
  DataModelReleaseEdge: Omit<DataModelReleaseEdge, 'node'> & { node: ResolversParentTypes['DataModelRelease'] };
  DataModelRevision: ModelRevisionRow;
  DataModelRevisionConnection: Omit<DataModelRevisionConnection, 'edges'> & { edges: Array<ResolversParentTypes['DataModelRevisionEdge']> };
  DataModelRevisionEdge: Omit<DataModelRevisionEdge, 'node'> & { node: ResolversParentTypes['DataModelRevision'] };
  Dataset: DatasetsRow;
  DatasetConnection: Omit<DatasetConnection, 'edges'> & { edges: Array<ResolversParentTypes['DatasetEdge']> };
  DatasetEdge: Omit<DatasetEdge, 'node'> & { node: ResolversParentTypes['Dataset'] };
  DatasetTypeDefinition: ResolversUnionTypes<ResolversParentTypes>['DatasetTypeDefinition'];
  DateTime: Scalars['DateTime']['output'];
  FinishRunInput: FinishRunInput;
  FinishRunPayload: Omit<FinishRunPayload, 'run'> & { run?: Maybe<ResolversParentTypes['Run']> };
  FinishStepInput: FinishStepInput;
  FinishStepPayload: Omit<FinishStepPayload, 'step'> & { step?: Maybe<ResolversParentTypes['Step']> };
  ID: Scalars['ID']['output'];
  Int: Scalars['Int']['output'];
  Invitation: InvitationsRow;
  InvitationConnection: Omit<InvitationConnection, 'edges'> & { edges: Array<ResolversParentTypes['InvitationEdge']> };
  InvitationEdge: Omit<InvitationEdge, 'node'> & { node: ResolversParentTypes['Invitation'] };
  JSON: Scalars['JSON']['output'];
  Materialization: MaterializationRow;
  MaterializationConnection: Omit<MaterializationConnection, 'edges'> & { edges: Array<ResolversParentTypes['MaterializationEdge']> };
  MaterializationEdge: Omit<MaterializationEdge, 'node'> & { node: ResolversParentTypes['Materialization'] };
  ModelColumnContext: ModelColumnContext;
  ModelColumnContextInput: ModelColumnContextInput;
  ModelContext: ModelContextsRow;
  Mutation: Record<PropertyKey, never>;
  Notebook: NotebooksRow;
  NotebookConnection: Omit<NotebookConnection, 'edges'> & { edges: Array<ResolversParentTypes['NotebookEdge']> };
  NotebookEdge: Omit<NotebookEdge, 'node'> & { node: ResolversParentTypes['Notebook'] };
  Organization: OrganizationsRow;
  OrganizationConnection: Omit<OrganizationConnection, 'edges'> & { edges: Array<ResolversParentTypes['OrganizationEdge']> };
  OrganizationEdge: Omit<OrganizationEdge, 'node'> & { node: ResolversParentTypes['Organization'] };
  OrganizationMember: Omit<OrganizationMember, 'user'> & { user: ResolversParentTypes['User'] };
  PageInfo: PageInfo;
  PreviewData: PreviewData;
  PublishNotebookPayload: Omit<PublishNotebookPayload, 'run'> & { run: ResolversParentTypes['Run'] };
  Query: Record<PropertyKey, never>;
  RemoveMemberInput: RemoveMemberInput;
  RemoveMemberPayload: RemoveMemberPayload;
  RevokeInvitationInput: RevokeInvitationInput;
  RevokeInvitationPayload: RevokeInvitationPayload;
  Run: RunRow;
  RunConnection: Omit<RunConnection, 'edges'> & { edges: Array<ResolversParentTypes['RunEdge']> };
  RunEdge: Omit<RunEdge, 'node'> & { node: ResolversParentTypes['Run'] };
  SaveNotebookPreviewInput: SaveNotebookPreviewInput;
  SaveNotebookPreviewPayload: Omit<SaveNotebookPreviewPayload, 'notebook'> & { notebook?: Maybe<ResolversParentTypes['Notebook']> };
  SavePublishedNotebookHtmlInput: SavePublishedNotebookHtmlInput;
  SavePublishedNotebookHtmlPayload: SavePublishedNotebookHtmlPayload;
  SimplePayload: SimplePayload;
  StartRunInput: StartRunInput;
  StartRunPayload: Omit<StartRunPayload, 'run'> & { run?: Maybe<ResolversParentTypes['Run']> };
  StartStepInput: StartStepInput;
  StartStepPayload: Omit<StartStepPayload, 'step'> & { step: ResolversParentTypes['Step'] };
  StaticModel: StaticModelRow;
  StaticModelConnection: Omit<StaticModelConnection, 'edges'> & { edges: Array<ResolversParentTypes['StaticModelEdge']> };
  StaticModelDefinition: Omit<StaticModelDefinition, 'staticModels'> & { staticModels: ResolversParentTypes['StaticModelConnection'] };
  StaticModelEdge: Omit<StaticModelEdge, 'node'> & { node: ResolversParentTypes['StaticModel'] };
  Step: StepRow;
  StepConnection: Omit<StepConnection, 'edges'> & { edges: Array<ResolversParentTypes['StepEdge']> };
  StepEdge: Omit<StepEdge, 'node'> & { node: ResolversParentTypes['Step'] };
  String: Scalars['String']['output'];
  SyncDataConnectionPayload: Omit<SyncDataConnectionPayload, 'run'> & { run: ResolversParentTypes['Run'] };
  System: System;
  SystemResolvedTableReference: SystemResolvedTableReference;
  Table: Omit<Table, 'columns' | 'dataset' | 'source'> & { columns: Array<ResolversParentTypes['TableColumn']>, dataset: ResolversParentTypes['Dataset'], source: ResolversParentTypes['TableSource'] };
  TableColumn: TableColumn;
  TableConnection: Omit<TableConnection, 'edges'> & { edges: Array<ResolversParentTypes['TableEdge']> };
  TableEdge: Omit<TableEdge, 'node'> & { node: ResolversParentTypes['Table'] };
  TableSource: ResolversUnionTypes<ResolversParentTypes>['TableSource'];
  UnpublishNotebookPayload: UnpublishNotebookPayload;
  UpdateDataModelInput: UpdateDataModelInput;
  UpdateDatasetInput: UpdateDatasetInput;
  UpdateDatasetPayload: Omit<UpdateDatasetPayload, 'dataset'> & { dataset?: Maybe<ResolversParentTypes['Dataset']> };
  UpdateMemberRoleInput: UpdateMemberRoleInput;
  UpdateMemberRolePayload: Omit<UpdateMemberRolePayload, 'member'> & { member?: Maybe<ResolversParentTypes['OrganizationMember']> };
  UpdateMetadataInput: UpdateMetadataInput;
  UpdateModelContextInput: UpdateModelContextInput;
  UpdateModelContextPayload: Omit<UpdateModelContextPayload, 'modelContext'> & { modelContext?: Maybe<ResolversParentTypes['ModelContext']> };
  UpdateNotebookInput: UpdateNotebookInput;
  UpdateNotebookPayload: Omit<UpdateNotebookPayload, 'notebook'> & { notebook?: Maybe<ResolversParentTypes['Notebook']> };
  UpdateRunMetadataInput: UpdateRunMetadataInput;
  UpdateRunMetadataPayload: Omit<UpdateRunMetadataPayload, 'run'> & { run?: Maybe<ResolversParentTypes['Run']> };
  UpdateStaticModelInput: UpdateStaticModelInput;
  User: UserProfilesRow;
  UserConnection: Omit<UserConnection, 'edges'> & { edges: Array<ResolversParentTypes['UserEdge']> };
  UserEdge: Omit<UserEdge, 'node'> & { node: ResolversParentTypes['User'] };
  Viewer: Omit<Viewer, 'datasets' | 'invitations' | 'notebooks' | 'organizations' | 'runs'> & { datasets: ResolversParentTypes['DatasetConnection'], invitations: ResolversParentTypes['InvitationConnection'], notebooks: ResolversParentTypes['NotebookConnection'], organizations: ResolversParentTypes['OrganizationConnection'], runs: ResolversParentTypes['RunConnection'] };
};

export type AcceptInvitationPayloadResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['AcceptInvitationPayload'] = ResolversParentTypes['AcceptInvitationPayload']> = {
  member?: Resolver<Maybe<ResolversTypes['OrganizationMember']>, ParentType, ContextType>;
  message?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  success?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
};

export type AddUserByEmailPayloadResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['AddUserByEmailPayload'] = ResolversParentTypes['AddUserByEmailPayload']> = {
  member?: Resolver<Maybe<ResolversTypes['OrganizationMember']>, ParentType, ContextType>;
  message?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  success?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
};

export type CancelRunPayloadResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['CancelRunPayload'] = ResolversParentTypes['CancelRunPayload']> = {
  message?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  run?: Resolver<Maybe<ResolversTypes['Run']>, ParentType, ContextType>;
  success?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
};

export type CreateDataConnectionPayloadResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['CreateDataConnectionPayload'] = ResolversParentTypes['CreateDataConnectionPayload']> = {
  dataConnection?: Resolver<Maybe<ResolversTypes['DataConnection']>, ParentType, ContextType>;
  message?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  success?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
};

export type CreateDataModelPayloadResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['CreateDataModelPayload'] = ResolversParentTypes['CreateDataModelPayload']> = {
  dataModel?: Resolver<Maybe<ResolversTypes['DataModel']>, ParentType, ContextType>;
  message?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  success?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
};

export type CreateDataModelReleasePayloadResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['CreateDataModelReleasePayload'] = ResolversParentTypes['CreateDataModelReleasePayload']> = {
  dataModelRelease?: Resolver<Maybe<ResolversTypes['DataModelRelease']>, ParentType, ContextType>;
  message?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  success?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
};

export type CreateDataModelRevisionPayloadResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['CreateDataModelRevisionPayload'] = ResolversParentTypes['CreateDataModelRevisionPayload']> = {
  dataModelRevision?: Resolver<Maybe<ResolversTypes['DataModelRevision']>, ParentType, ContextType>;
  message?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  success?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
};

export type CreateDatasetPayloadResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['CreateDatasetPayload'] = ResolversParentTypes['CreateDatasetPayload']> = {
  dataset?: Resolver<Maybe<ResolversTypes['Dataset']>, ParentType, ContextType>;
  message?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  success?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
};

export type CreateInvitationPayloadResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['CreateInvitationPayload'] = ResolversParentTypes['CreateInvitationPayload']> = {
  invitation?: Resolver<Maybe<ResolversTypes['Invitation']>, ParentType, ContextType>;
  message?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  success?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
};

export type CreateMaterializationPayloadResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['CreateMaterializationPayload'] = ResolversParentTypes['CreateMaterializationPayload']> = {
  materialization?: Resolver<ResolversTypes['Materialization'], ParentType, ContextType>;
  message?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  success?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
};

export type CreateNotebookPayloadResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['CreateNotebookPayload'] = ResolversParentTypes['CreateNotebookPayload']> = {
  message?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  notebook?: Resolver<Maybe<ResolversTypes['Notebook']>, ParentType, ContextType>;
  success?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
};

export type CreateRunRequestPayloadResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['CreateRunRequestPayload'] = ResolversParentTypes['CreateRunRequestPayload']> = {
  message?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  run?: Resolver<ResolversTypes['Run'], ParentType, ContextType>;
  success?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
};

export type CreateStaticModelPayloadResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['CreateStaticModelPayload'] = ResolversParentTypes['CreateStaticModelPayload']> = {
  message?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  staticModel?: Resolver<Maybe<ResolversTypes['StaticModel']>, ParentType, ContextType>;
  success?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
};

export type DataConnectionResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['DataConnection'] = ResolversParentTypes['DataConnection']> = {
  config?: Resolver<ResolversTypes['JSON'], ParentType, ContextType>;
  createdAt?: Resolver<ResolversTypes['DateTime'], ParentType, ContextType>;
  id?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  name?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  orgId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  organization?: Resolver<ResolversTypes['Organization'], ParentType, ContextType>;
  type?: Resolver<ResolversTypes['DataConnectionType'], ParentType, ContextType>;
  updatedAt?: Resolver<ResolversTypes['DateTime'], ParentType, ContextType>;
  __isTypeOf?: IsTypeOfResolverFn<ParentType, ContextType>;
};

export type DataConnectionAliasResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['DataConnectionAlias'] = ResolversParentTypes['DataConnectionAlias']> = {
  dataConnectionId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  datasetId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  id?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  materializations?: Resolver<ResolversTypes['MaterializationConnection'], ParentType, ContextType, RequireFields<DataConnectionAliasMaterializationsArgs, 'first' | 'tableName'>>;
  modelContext?: Resolver<Maybe<ResolversTypes['ModelContext']>, ParentType, ContextType, RequireFields<DataConnectionAliasModelContextArgs, 'tableName'>>;
  orgId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  previewData?: Resolver<ResolversTypes['PreviewData'], ParentType, ContextType, RequireFields<DataConnectionAliasPreviewDataArgs, 'tableName'>>;
  schema?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
};

export type DataConnectionConnectionResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['DataConnectionConnection'] = ResolversParentTypes['DataConnectionConnection']> = {
  edges?: Resolver<Array<ResolversTypes['DataConnectionEdge']>, ParentType, ContextType>;
  pageInfo?: Resolver<ResolversTypes['PageInfo'], ParentType, ContextType>;
  totalCount?: Resolver<Maybe<ResolversTypes['Int']>, ParentType, ContextType>;
};

export type DataConnectionDefinitionResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['DataConnectionDefinition'] = ResolversParentTypes['DataConnectionDefinition']> = {
  dataConnectionAlias?: Resolver<ResolversTypes['DataConnectionAlias'], ParentType, ContextType>;
  datasetId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  orgId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  __isTypeOf?: IsTypeOfResolverFn<ParentType, ContextType>;
};

export type DataConnectionEdgeResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['DataConnectionEdge'] = ResolversParentTypes['DataConnectionEdge']> = {
  cursor?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  node?: Resolver<ResolversTypes['DataConnection'], ParentType, ContextType>;
};

export type DataConnectionSchemaResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['DataConnectionSchema'] = ResolversParentTypes['DataConnectionSchema']> = {
  name?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  tables?: Resolver<Array<ResolversTypes['DataConnectionTable']>, ParentType, ContextType>;
};

export type DataConnectionTableResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['DataConnectionTable'] = ResolversParentTypes['DataConnectionTable']> = {
  name?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  schema?: Resolver<Array<ResolversTypes['DataModelColumn']>, ParentType, ContextType>;
};

export type DataIngestionResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['DataIngestion'] = ResolversParentTypes['DataIngestion']> = {
  config?: Resolver<ResolversTypes['JSON'], ParentType, ContextType>;
  createdAt?: Resolver<ResolversTypes['DateTime'], ParentType, ContextType>;
  datasetId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  factoryType?: Resolver<ResolversTypes['DataIngestionFactoryType'], ParentType, ContextType>;
  id?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  materializations?: Resolver<ResolversTypes['MaterializationConnection'], ParentType, ContextType, RequireFields<DataIngestionMaterializationsArgs, 'first' | 'tableName'>>;
  modelContext?: Resolver<Maybe<ResolversTypes['ModelContext']>, ParentType, ContextType, RequireFields<DataIngestionModelContextArgs, 'tableName'>>;
  orgId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  previewData?: Resolver<ResolversTypes['PreviewData'], ParentType, ContextType, RequireFields<DataIngestionPreviewDataArgs, 'tableName'>>;
  updatedAt?: Resolver<ResolversTypes['DateTime'], ParentType, ContextType>;
  __isTypeOf?: IsTypeOfResolverFn<ParentType, ContextType>;
};

export type DataIngestionConnectionResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['DataIngestionConnection'] = ResolversParentTypes['DataIngestionConnection']> = {
  edges?: Resolver<Array<ResolversTypes['DataIngestionEdge']>, ParentType, ContextType>;
  pageInfo?: Resolver<ResolversTypes['PageInfo'], ParentType, ContextType>;
  totalCount?: Resolver<Maybe<ResolversTypes['Int']>, ParentType, ContextType>;
};

export type DataIngestionDefinitionResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['DataIngestionDefinition'] = ResolversParentTypes['DataIngestionDefinition']> = {
  dataIngestion?: Resolver<Maybe<ResolversTypes['DataIngestion']>, ParentType, ContextType>;
  datasetId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  orgId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  __isTypeOf?: IsTypeOfResolverFn<ParentType, ContextType>;
};

export type DataIngestionEdgeResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['DataIngestionEdge'] = ResolversParentTypes['DataIngestionEdge']> = {
  cursor?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  node?: Resolver<ResolversTypes['DataIngestion'], ParentType, ContextType>;
};

export type DataModelResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['DataModel'] = ResolversParentTypes['DataModel']> = {
  createdAt?: Resolver<ResolversTypes['DateTime'], ParentType, ContextType>;
  dataset?: Resolver<ResolversTypes['Dataset'], ParentType, ContextType>;
  id?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  isEnabled?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
  latestRelease?: Resolver<Maybe<ResolversTypes['DataModelRelease']>, ParentType, ContextType>;
  latestRevision?: Resolver<Maybe<ResolversTypes['DataModelRevision']>, ParentType, ContextType>;
  materializations?: Resolver<ResolversTypes['MaterializationConnection'], ParentType, ContextType, RequireFields<DataModelMaterializationsArgs, 'first'>>;
  modelContext?: Resolver<Maybe<ResolversTypes['ModelContext']>, ParentType, ContextType>;
  name?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  orgId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  organization?: Resolver<ResolversTypes['Organization'], ParentType, ContextType>;
  previewData?: Resolver<ResolversTypes['PreviewData'], ParentType, ContextType>;
  releases?: Resolver<ResolversTypes['DataModelReleaseConnection'], ParentType, ContextType, RequireFields<DataModelReleasesArgs, 'first'>>;
  revisions?: Resolver<ResolversTypes['DataModelRevisionConnection'], ParentType, ContextType, RequireFields<DataModelRevisionsArgs, 'first'>>;
  runs?: Resolver<ResolversTypes['RunConnection'], ParentType, ContextType, RequireFields<DataModelRunsArgs, 'first'>>;
  updatedAt?: Resolver<ResolversTypes['DateTime'], ParentType, ContextType>;
  __isTypeOf?: IsTypeOfResolverFn<ParentType, ContextType>;
};

export type DataModelColumnResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['DataModelColumn'] = ResolversParentTypes['DataModelColumn']> = {
  description?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  name?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  type?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
};

export type DataModelConnectionResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['DataModelConnection'] = ResolversParentTypes['DataModelConnection']> = {
  edges?: Resolver<Array<ResolversTypes['DataModelEdge']>, ParentType, ContextType>;
  pageInfo?: Resolver<ResolversTypes['PageInfo'], ParentType, ContextType>;
  totalCount?: Resolver<Maybe<ResolversTypes['Int']>, ParentType, ContextType>;
};

export type DataModelDefinitionResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['DataModelDefinition'] = ResolversParentTypes['DataModelDefinition']> = {
  dataModels?: Resolver<ResolversTypes['DataModelConnection'], ParentType, ContextType, RequireFields<DataModelDefinitionDataModelsArgs, 'first'>>;
  datasetId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  orgId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  __isTypeOf?: IsTypeOfResolverFn<ParentType, ContextType>;
};

export type DataModelDependencyResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['DataModelDependency'] = ResolversParentTypes['DataModelDependency']> = {
  alias?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  tableId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
};

export type DataModelEdgeResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['DataModelEdge'] = ResolversParentTypes['DataModelEdge']> = {
  cursor?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  node?: Resolver<ResolversTypes['DataModel'], ParentType, ContextType>;
};

export type DataModelKindOptionsResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['DataModelKindOptions'] = ResolversParentTypes['DataModelKindOptions']> = {
  batchSize?: Resolver<Maybe<ResolversTypes['Int']>, ParentType, ContextType>;
  executionTimeAsValidFrom?: Resolver<Maybe<ResolversTypes['Boolean']>, ParentType, ContextType>;
  invalidateHardDeletes?: Resolver<Maybe<ResolversTypes['Boolean']>, ParentType, ContextType>;
  lookback?: Resolver<Maybe<ResolversTypes['Int']>, ParentType, ContextType>;
  mergeFilter?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  scdColumns?: Resolver<Maybe<Array<ResolversTypes['String']>>, ParentType, ContextType>;
  timeColumn?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  timeColumnFormat?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  uniqueKeyColumns?: Resolver<Maybe<Array<ResolversTypes['String']>>, ParentType, ContextType>;
  updatedAtAsValidFrom?: Resolver<Maybe<ResolversTypes['Boolean']>, ParentType, ContextType>;
  updatedAtColumn?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  validFromName?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  validToName?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  whenMatchedSql?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
};

export type DataModelReleaseResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['DataModelRelease'] = ResolversParentTypes['DataModelRelease']> = {
  createdAt?: Resolver<ResolversTypes['DateTime'], ParentType, ContextType>;
  dataModel?: Resolver<ResolversTypes['DataModel'], ParentType, ContextType>;
  dataModelId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  description?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  id?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  orgId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  organization?: Resolver<ResolversTypes['Organization'], ParentType, ContextType>;
  revision?: Resolver<ResolversTypes['DataModelRevision'], ParentType, ContextType>;
  revisionId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  updatedAt?: Resolver<ResolversTypes['DateTime'], ParentType, ContextType>;
};

export type DataModelReleaseConnectionResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['DataModelReleaseConnection'] = ResolversParentTypes['DataModelReleaseConnection']> = {
  edges?: Resolver<Array<ResolversTypes['DataModelReleaseEdge']>, ParentType, ContextType>;
  pageInfo?: Resolver<ResolversTypes['PageInfo'], ParentType, ContextType>;
  totalCount?: Resolver<Maybe<ResolversTypes['Int']>, ParentType, ContextType>;
};

export type DataModelReleaseEdgeResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['DataModelReleaseEdge'] = ResolversParentTypes['DataModelReleaseEdge']> = {
  cursor?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  node?: Resolver<ResolversTypes['DataModelRelease'], ParentType, ContextType>;
};

export type DataModelRevisionResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['DataModelRevision'] = ResolversParentTypes['DataModelRevision']> = {
  clusteredBy?: Resolver<Maybe<Array<ResolversTypes['String']>>, ParentType, ContextType>;
  code?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  createdAt?: Resolver<ResolversTypes['DateTime'], ParentType, ContextType>;
  cron?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  dataModel?: Resolver<ResolversTypes['DataModel'], ParentType, ContextType>;
  dataModelId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  dependsOn?: Resolver<Maybe<Array<ResolversTypes['DataModelDependency']>>, ParentType, ContextType>;
  description?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  end?: Resolver<Maybe<ResolversTypes['DateTime']>, ParentType, ContextType>;
  hash?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  id?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  kind?: Resolver<ResolversTypes['DataModelKind'], ParentType, ContextType>;
  kindOptions?: Resolver<Maybe<ResolversTypes['DataModelKindOptions']>, ParentType, ContextType>;
  language?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  name?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  orgId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  organization?: Resolver<ResolversTypes['Organization'], ParentType, ContextType>;
  partitionedBy?: Resolver<Maybe<Array<ResolversTypes['String']>>, ParentType, ContextType>;
  revisionNumber?: Resolver<ResolversTypes['Int'], ParentType, ContextType>;
  schema?: Resolver<Maybe<Array<ResolversTypes['DataModelColumn']>>, ParentType, ContextType>;
  start?: Resolver<Maybe<ResolversTypes['DateTime']>, ParentType, ContextType>;
};

export type DataModelRevisionConnectionResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['DataModelRevisionConnection'] = ResolversParentTypes['DataModelRevisionConnection']> = {
  edges?: Resolver<Array<ResolversTypes['DataModelRevisionEdge']>, ParentType, ContextType>;
  pageInfo?: Resolver<ResolversTypes['PageInfo'], ParentType, ContextType>;
  totalCount?: Resolver<Maybe<ResolversTypes['Int']>, ParentType, ContextType>;
};

export type DataModelRevisionEdgeResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['DataModelRevisionEdge'] = ResolversParentTypes['DataModelRevisionEdge']> = {
  cursor?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  node?: Resolver<ResolversTypes['DataModelRevision'], ParentType, ContextType>;
};

export type DatasetResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['Dataset'] = ResolversParentTypes['Dataset']> = {
  createdAt?: Resolver<ResolversTypes['DateTime'], ParentType, ContextType>;
  creator?: Resolver<ResolversTypes['User'], ParentType, ContextType>;
  creatorId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  description?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  displayName?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  id?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  materializations?: Resolver<ResolversTypes['MaterializationConnection'], ParentType, ContextType, RequireFields<DatasetMaterializationsArgs, 'first'>>;
  name?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  orgId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  organization?: Resolver<ResolversTypes['Organization'], ParentType, ContextType>;
  runs?: Resolver<ResolversTypes['RunConnection'], ParentType, ContextType, RequireFields<DatasetRunsArgs, 'first'>>;
  tables?: Resolver<ResolversTypes['TableConnection'], ParentType, ContextType, RequireFields<DatasetTablesArgs, 'first'>>;
  type?: Resolver<ResolversTypes['DatasetType'], ParentType, ContextType>;
  typeDefinition?: Resolver<ResolversTypes['DatasetTypeDefinition'], ParentType, ContextType>;
  updatedAt?: Resolver<ResolversTypes['DateTime'], ParentType, ContextType>;
};

export type DatasetConnectionResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['DatasetConnection'] = ResolversParentTypes['DatasetConnection']> = {
  edges?: Resolver<Array<ResolversTypes['DatasetEdge']>, ParentType, ContextType>;
  pageInfo?: Resolver<ResolversTypes['PageInfo'], ParentType, ContextType>;
  totalCount?: Resolver<Maybe<ResolversTypes['Int']>, ParentType, ContextType>;
};

export type DatasetEdgeResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['DatasetEdge'] = ResolversParentTypes['DatasetEdge']> = {
  cursor?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  node?: Resolver<ResolversTypes['Dataset'], ParentType, ContextType>;
};

export type DatasetTypeDefinitionResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['DatasetTypeDefinition'] = ResolversParentTypes['DatasetTypeDefinition']> = {
  __resolveType: TypeResolveFn<'DataConnectionDefinition' | 'DataIngestionDefinition' | 'DataModelDefinition' | 'StaticModelDefinition', ParentType, ContextType>;
};

export interface DateTimeScalarConfig extends GraphQLScalarTypeConfig<ResolversTypes['DateTime'], any> {
  name: 'DateTime';
}

export type FinishRunPayloadResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['FinishRunPayload'] = ResolversParentTypes['FinishRunPayload']> = {
  message?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  run?: Resolver<Maybe<ResolversTypes['Run']>, ParentType, ContextType>;
  success?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
};

export type FinishStepPayloadResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['FinishStepPayload'] = ResolversParentTypes['FinishStepPayload']> = {
  message?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  step?: Resolver<Maybe<ResolversTypes['Step']>, ParentType, ContextType>;
  success?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
};

export type InvitationResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['Invitation'] = ResolversParentTypes['Invitation']> = {
  acceptedAt?: Resolver<Maybe<ResolversTypes['DateTime']>, ParentType, ContextType>;
  acceptedBy?: Resolver<Maybe<ResolversTypes['User']>, ParentType, ContextType>;
  createdAt?: Resolver<ResolversTypes['DateTime'], ParentType, ContextType>;
  deletedAt?: Resolver<Maybe<ResolversTypes['DateTime']>, ParentType, ContextType>;
  email?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  expiresAt?: Resolver<ResolversTypes['DateTime'], ParentType, ContextType>;
  id?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  invitedBy?: Resolver<ResolversTypes['User'], ParentType, ContextType>;
  orgId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  organization?: Resolver<ResolversTypes['Organization'], ParentType, ContextType>;
  status?: Resolver<ResolversTypes['InvitationStatus'], ParentType, ContextType>;
  userRole?: Resolver<ResolversTypes['MemberRole'], ParentType, ContextType>;
};

export type InvitationConnectionResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['InvitationConnection'] = ResolversParentTypes['InvitationConnection']> = {
  edges?: Resolver<Array<ResolversTypes['InvitationEdge']>, ParentType, ContextType>;
  pageInfo?: Resolver<ResolversTypes['PageInfo'], ParentType, ContextType>;
  totalCount?: Resolver<Maybe<ResolversTypes['Int']>, ParentType, ContextType>;
};

export type InvitationEdgeResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['InvitationEdge'] = ResolversParentTypes['InvitationEdge']> = {
  cursor?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  node?: Resolver<ResolversTypes['Invitation'], ParentType, ContextType>;
};

export interface JsonScalarConfig extends GraphQLScalarTypeConfig<ResolversTypes['JSON'], any> {
  name: 'JSON';
}

export type MaterializationResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['Materialization'] = ResolversParentTypes['Materialization']> = {
  createdAt?: Resolver<ResolversTypes['DateTime'], ParentType, ContextType>;
  datasetId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  id?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  run?: Resolver<ResolversTypes['Run'], ParentType, ContextType>;
  runId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  schema?: Resolver<Maybe<Array<ResolversTypes['DataModelColumn']>>, ParentType, ContextType>;
  step?: Resolver<ResolversTypes['Step'], ParentType, ContextType>;
  stepId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
};

export type MaterializationConnectionResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['MaterializationConnection'] = ResolversParentTypes['MaterializationConnection']> = {
  edges?: Resolver<Array<ResolversTypes['MaterializationEdge']>, ParentType, ContextType>;
  pageInfo?: Resolver<ResolversTypes['PageInfo'], ParentType, ContextType>;
  totalCount?: Resolver<Maybe<ResolversTypes['Int']>, ParentType, ContextType>;
};

export type MaterializationEdgeResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['MaterializationEdge'] = ResolversParentTypes['MaterializationEdge']> = {
  cursor?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  node?: Resolver<ResolversTypes['Materialization'], ParentType, ContextType>;
};

export type ModelColumnContextResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['ModelColumnContext'] = ResolversParentTypes['ModelColumnContext']> = {
  context?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  name?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
};

export type ModelContextResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['ModelContext'] = ResolversParentTypes['ModelContext']> = {
  columnContext?: Resolver<Maybe<Array<ResolversTypes['ModelColumnContext']>>, ParentType, ContextType>;
  context?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  createdAt?: Resolver<ResolversTypes['DateTime'], ParentType, ContextType>;
  datasetId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  id?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  orgId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  tableId?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  updatedAt?: Resolver<ResolversTypes['DateTime'], ParentType, ContextType>;
};

export type MutationResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['Mutation'] = ResolversParentTypes['Mutation']> = {
  _empty?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  acceptInvitation?: Resolver<ResolversTypes['AcceptInvitationPayload'], ParentType, ContextType, RequireFields<MutationAcceptInvitationArgs, 'input'>>;
  addUserByEmail?: Resolver<ResolversTypes['AddUserByEmailPayload'], ParentType, ContextType, RequireFields<MutationAddUserByEmailArgs, 'input'>>;
  cancelRun?: Resolver<ResolversTypes['CancelRunPayload'], ParentType, ContextType, RequireFields<MutationCancelRunArgs, 'input'>>;
  createDataConnection?: Resolver<ResolversTypes['CreateDataConnectionPayload'], ParentType, ContextType, RequireFields<MutationCreateDataConnectionArgs, 'input'>>;
  createDataConnectionDatasets?: Resolver<ResolversTypes['SimplePayload'], ParentType, ContextType, RequireFields<MutationCreateDataConnectionDatasetsArgs, 'input'>>;
  createDataConnectionRunRequest?: Resolver<ResolversTypes['CreateRunRequestPayload'], ParentType, ContextType, RequireFields<MutationCreateDataConnectionRunRequestArgs, 'input'>>;
  createDataIngestionConfig?: Resolver<ResolversTypes['DataIngestion'], ParentType, ContextType, RequireFields<MutationCreateDataIngestionConfigArgs, 'input'>>;
  createDataIngestionRunRequest?: Resolver<ResolversTypes['CreateRunRequestPayload'], ParentType, ContextType, RequireFields<MutationCreateDataIngestionRunRequestArgs, 'input'>>;
  createDataModel?: Resolver<ResolversTypes['CreateDataModelPayload'], ParentType, ContextType, RequireFields<MutationCreateDataModelArgs, 'input'>>;
  createDataModelRelease?: Resolver<ResolversTypes['CreateDataModelReleasePayload'], ParentType, ContextType, RequireFields<MutationCreateDataModelReleaseArgs, 'input'>>;
  createDataModelRevision?: Resolver<ResolversTypes['CreateDataModelRevisionPayload'], ParentType, ContextType, RequireFields<MutationCreateDataModelRevisionArgs, 'input'>>;
  createDataset?: Resolver<ResolversTypes['CreateDatasetPayload'], ParentType, ContextType, RequireFields<MutationCreateDatasetArgs, 'input'>>;
  createInvitation?: Resolver<ResolversTypes['CreateInvitationPayload'], ParentType, ContextType, RequireFields<MutationCreateInvitationArgs, 'input'>>;
  createMaterialization?: Resolver<ResolversTypes['CreateMaterializationPayload'], ParentType, ContextType, RequireFields<MutationCreateMaterializationArgs, 'input'>>;
  createNotebook?: Resolver<ResolversTypes['CreateNotebookPayload'], ParentType, ContextType, RequireFields<MutationCreateNotebookArgs, 'input'>>;
  createStaticModel?: Resolver<ResolversTypes['CreateStaticModelPayload'], ParentType, ContextType, RequireFields<MutationCreateStaticModelArgs, 'input'>>;
  createStaticModelRunRequest?: Resolver<ResolversTypes['CreateRunRequestPayload'], ParentType, ContextType, RequireFields<MutationCreateStaticModelRunRequestArgs, 'input'>>;
  createStaticModelUploadUrl?: Resolver<ResolversTypes['String'], ParentType, ContextType, RequireFields<MutationCreateStaticModelUploadUrlArgs, 'staticModelId'>>;
  createUserModelRunRequest?: Resolver<ResolversTypes['CreateRunRequestPayload'], ParentType, ContextType, RequireFields<MutationCreateUserModelRunRequestArgs, 'input'>>;
  deleteDataConnection?: Resolver<ResolversTypes['SimplePayload'], ParentType, ContextType, RequireFields<MutationDeleteDataConnectionArgs, 'id'>>;
  deleteDataModel?: Resolver<ResolversTypes['SimplePayload'], ParentType, ContextType, RequireFields<MutationDeleteDataModelArgs, 'id'>>;
  deleteDataset?: Resolver<ResolversTypes['SimplePayload'], ParentType, ContextType, RequireFields<MutationDeleteDatasetArgs, 'id'>>;
  deleteStaticModel?: Resolver<ResolversTypes['SimplePayload'], ParentType, ContextType, RequireFields<MutationDeleteStaticModelArgs, 'id'>>;
  finishRun?: Resolver<ResolversTypes['FinishRunPayload'], ParentType, ContextType, RequireFields<MutationFinishRunArgs, 'input'>>;
  finishStep?: Resolver<ResolversTypes['FinishStepPayload'], ParentType, ContextType, RequireFields<MutationFinishStepArgs, 'input'>>;
  publishNotebook?: Resolver<ResolversTypes['PublishNotebookPayload'], ParentType, ContextType, RequireFields<MutationPublishNotebookArgs, 'notebookId'>>;
  removeMember?: Resolver<ResolversTypes['RemoveMemberPayload'], ParentType, ContextType, RequireFields<MutationRemoveMemberArgs, 'input'>>;
  revokeInvitation?: Resolver<ResolversTypes['RevokeInvitationPayload'], ParentType, ContextType, RequireFields<MutationRevokeInvitationArgs, 'input'>>;
  saveNotebookPreview?: Resolver<ResolversTypes['SaveNotebookPreviewPayload'], ParentType, ContextType, RequireFields<MutationSaveNotebookPreviewArgs, 'input'>>;
  savePublishedNotebookHtml?: Resolver<ResolversTypes['SavePublishedNotebookHtmlPayload'], ParentType, ContextType, RequireFields<MutationSavePublishedNotebookHtmlArgs, 'input'>>;
  startRun?: Resolver<ResolversTypes['StartRunPayload'], ParentType, ContextType, RequireFields<MutationStartRunArgs, 'input'>>;
  startStep?: Resolver<ResolversTypes['StartStepPayload'], ParentType, ContextType, RequireFields<MutationStartStepArgs, 'input'>>;
  syncDataConnection?: Resolver<ResolversTypes['SyncDataConnectionPayload'], ParentType, ContextType, RequireFields<MutationSyncDataConnectionArgs, 'id'>>;
  unpublishNotebook?: Resolver<ResolversTypes['UnpublishNotebookPayload'], ParentType, ContextType, RequireFields<MutationUnpublishNotebookArgs, 'notebookId'>>;
  updateDataModel?: Resolver<ResolversTypes['CreateDataModelPayload'], ParentType, ContextType, RequireFields<MutationUpdateDataModelArgs, 'input'>>;
  updateDataset?: Resolver<ResolversTypes['UpdateDatasetPayload'], ParentType, ContextType, RequireFields<MutationUpdateDatasetArgs, 'input'>>;
  updateMemberRole?: Resolver<ResolversTypes['UpdateMemberRolePayload'], ParentType, ContextType, RequireFields<MutationUpdateMemberRoleArgs, 'input'>>;
  updateModelContext?: Resolver<ResolversTypes['UpdateModelContextPayload'], ParentType, ContextType, RequireFields<MutationUpdateModelContextArgs, 'input'>>;
  updateNotebook?: Resolver<ResolversTypes['UpdateNotebookPayload'], ParentType, ContextType, RequireFields<MutationUpdateNotebookArgs, 'input'>>;
  updateRunMetadata?: Resolver<ResolversTypes['UpdateRunMetadataPayload'], ParentType, ContextType, RequireFields<MutationUpdateRunMetadataArgs, 'input'>>;
  updateStaticModel?: Resolver<ResolversTypes['CreateStaticModelPayload'], ParentType, ContextType, RequireFields<MutationUpdateStaticModelArgs, 'input'>>;
};

export type NotebookResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['Notebook'] = ResolversParentTypes['Notebook']> = {
  createdAt?: Resolver<ResolversTypes['DateTime'], ParentType, ContextType>;
  creator?: Resolver<ResolversTypes['User'], ParentType, ContextType>;
  creatorId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  data?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  description?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  id?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  name?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  orgId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  organization?: Resolver<ResolversTypes['Organization'], ParentType, ContextType>;
  preview?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  updatedAt?: Resolver<ResolversTypes['DateTime'], ParentType, ContextType>;
};

export type NotebookConnectionResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['NotebookConnection'] = ResolversParentTypes['NotebookConnection']> = {
  edges?: Resolver<Array<ResolversTypes['NotebookEdge']>, ParentType, ContextType>;
  pageInfo?: Resolver<ResolversTypes['PageInfo'], ParentType, ContextType>;
  totalCount?: Resolver<Maybe<ResolversTypes['Int']>, ParentType, ContextType>;
};

export type NotebookEdgeResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['NotebookEdge'] = ResolversParentTypes['NotebookEdge']> = {
  cursor?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  node?: Resolver<ResolversTypes['Notebook'], ParentType, ContextType>;
};

export type OrganizationResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['Organization'] = ResolversParentTypes['Organization']> = {
  createdAt?: Resolver<ResolversTypes['DateTime'], ParentType, ContextType>;
  dataConnections?: Resolver<ResolversTypes['DataConnectionConnection'], ParentType, ContextType, RequireFields<OrganizationDataConnectionsArgs, 'first'>>;
  datasets?: Resolver<ResolversTypes['DatasetConnection'], ParentType, ContextType, RequireFields<OrganizationDatasetsArgs, 'first'>>;
  description?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  displayName?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  id?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  members?: Resolver<ResolversTypes['UserConnection'], ParentType, ContextType, RequireFields<OrganizationMembersArgs, 'first'>>;
  name?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  notebooks?: Resolver<ResolversTypes['NotebookConnection'], ParentType, ContextType, RequireFields<OrganizationNotebooksArgs, 'first'>>;
  updatedAt?: Resolver<ResolversTypes['DateTime'], ParentType, ContextType>;
};

export type OrganizationConnectionResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['OrganizationConnection'] = ResolversParentTypes['OrganizationConnection']> = {
  edges?: Resolver<Array<ResolversTypes['OrganizationEdge']>, ParentType, ContextType>;
  pageInfo?: Resolver<ResolversTypes['PageInfo'], ParentType, ContextType>;
  totalCount?: Resolver<Maybe<ResolversTypes['Int']>, ParentType, ContextType>;
};

export type OrganizationEdgeResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['OrganizationEdge'] = ResolversParentTypes['OrganizationEdge']> = {
  cursor?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  node?: Resolver<ResolversTypes['Organization'], ParentType, ContextType>;
};

export type OrganizationMemberResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['OrganizationMember'] = ResolversParentTypes['OrganizationMember']> = {
  createdAt?: Resolver<ResolversTypes['DateTime'], ParentType, ContextType>;
  id?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  orgId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  user?: Resolver<ResolversTypes['User'], ParentType, ContextType>;
  userId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  userRole?: Resolver<ResolversTypes['MemberRole'], ParentType, ContextType>;
};

export type PageInfoResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['PageInfo'] = ResolversParentTypes['PageInfo']> = {
  endCursor?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  hasNextPage?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
  hasPreviousPage?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
  startCursor?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
};

export type PreviewDataResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['PreviewData'] = ResolversParentTypes['PreviewData']> = {
  isAvailable?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
  rows?: Resolver<Array<ResolversTypes['JSON']>, ParentType, ContextType>;
};

export type PublishNotebookPayloadResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['PublishNotebookPayload'] = ResolversParentTypes['PublishNotebookPayload']> = {
  message?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  run?: Resolver<ResolversTypes['Run'], ParentType, ContextType>;
  success?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
};

export type QueryResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['Query'] = ResolversParentTypes['Query']> = {
  _empty?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  dataConnections?: Resolver<ResolversTypes['DataConnectionConnection'], ParentType, ContextType, RequireFields<QueryDataConnectionsArgs, 'first'>>;
  dataModels?: Resolver<ResolversTypes['DataModelConnection'], ParentType, ContextType, RequireFields<QueryDataModelsArgs, 'first'>>;
  datasets?: Resolver<ResolversTypes['DatasetConnection'], ParentType, ContextType, RequireFields<QueryDatasetsArgs, 'first'>>;
  invitations?: Resolver<ResolversTypes['InvitationConnection'], ParentType, ContextType, RequireFields<QueryInvitationsArgs, 'first'>>;
  notebooks?: Resolver<ResolversTypes['NotebookConnection'], ParentType, ContextType, RequireFields<QueryNotebooksArgs, 'first'>>;
  organizations?: Resolver<ResolversTypes['OrganizationConnection'], ParentType, ContextType, RequireFields<QueryOrganizationsArgs, 'first'>>;
  runs?: Resolver<ResolversTypes['RunConnection'], ParentType, ContextType, RequireFields<QueryRunsArgs, 'first'>>;
  staticModels?: Resolver<ResolversTypes['StaticModelConnection'], ParentType, ContextType, RequireFields<QueryStaticModelsArgs, 'first'>>;
  system?: Resolver<ResolversTypes['System'], ParentType, ContextType>;
  viewer?: Resolver<ResolversTypes['Viewer'], ParentType, ContextType>;
};

export type RemoveMemberPayloadResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['RemoveMemberPayload'] = ResolversParentTypes['RemoveMemberPayload']> = {
  message?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  success?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
};

export type RevokeInvitationPayloadResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['RevokeInvitationPayload'] = ResolversParentTypes['RevokeInvitationPayload']> = {
  message?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  success?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
};

export type RunResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['Run'] = ResolversParentTypes['Run']> = {
  dataset?: Resolver<Maybe<ResolversTypes['Dataset']>, ParentType, ContextType>;
  datasetId?: Resolver<Maybe<ResolversTypes['ID']>, ParentType, ContextType>;
  finishedAt?: Resolver<Maybe<ResolversTypes['DateTime']>, ParentType, ContextType>;
  id?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  logsUrl?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  metadata?: Resolver<Maybe<ResolversTypes['JSON']>, ParentType, ContextType>;
  orgId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  organization?: Resolver<ResolversTypes['Organization'], ParentType, ContextType>;
  queuedAt?: Resolver<ResolversTypes['DateTime'], ParentType, ContextType>;
  requestedBy?: Resolver<Maybe<ResolversTypes['User']>, ParentType, ContextType>;
  runType?: Resolver<ResolversTypes['RunType'], ParentType, ContextType>;
  startedAt?: Resolver<Maybe<ResolversTypes['DateTime']>, ParentType, ContextType>;
  status?: Resolver<ResolversTypes['RunStatus'], ParentType, ContextType>;
  steps?: Resolver<ResolversTypes['StepConnection'], ParentType, ContextType>;
  triggerType?: Resolver<ResolversTypes['RunTriggerType'], ParentType, ContextType>;
};

export type RunConnectionResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['RunConnection'] = ResolversParentTypes['RunConnection']> = {
  edges?: Resolver<Array<ResolversTypes['RunEdge']>, ParentType, ContextType>;
  pageInfo?: Resolver<ResolversTypes['PageInfo'], ParentType, ContextType>;
  totalCount?: Resolver<Maybe<ResolversTypes['Int']>, ParentType, ContextType>;
};

export type RunEdgeResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['RunEdge'] = ResolversParentTypes['RunEdge']> = {
  cursor?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  node?: Resolver<ResolversTypes['Run'], ParentType, ContextType>;
};

export type SaveNotebookPreviewPayloadResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['SaveNotebookPreviewPayload'] = ResolversParentTypes['SaveNotebookPreviewPayload']> = {
  message?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  notebook?: Resolver<Maybe<ResolversTypes['Notebook']>, ParentType, ContextType>;
  previewUrl?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  success?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
};

export type SavePublishedNotebookHtmlPayloadResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['SavePublishedNotebookHtmlPayload'] = ResolversParentTypes['SavePublishedNotebookHtmlPayload']> = {
  message?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  success?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
};

export type SimplePayloadResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['SimplePayload'] = ResolversParentTypes['SimplePayload']> = {
  message?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  success?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
};

export type StartRunPayloadResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['StartRunPayload'] = ResolversParentTypes['StartRunPayload']> = {
  message?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  run?: Resolver<Maybe<ResolversTypes['Run']>, ParentType, ContextType>;
  success?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
};

export type StartStepPayloadResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['StartStepPayload'] = ResolversParentTypes['StartStepPayload']> = {
  message?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  step?: Resolver<ResolversTypes['Step'], ParentType, ContextType>;
  success?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
};

export type StaticModelResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['StaticModel'] = ResolversParentTypes['StaticModel']> = {
  createdAt?: Resolver<ResolversTypes['DateTime'], ParentType, ContextType>;
  dataset?: Resolver<ResolversTypes['Dataset'], ParentType, ContextType>;
  id?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  materializations?: Resolver<ResolversTypes['MaterializationConnection'], ParentType, ContextType, RequireFields<StaticModelMaterializationsArgs, 'first'>>;
  modelContext?: Resolver<Maybe<ResolversTypes['ModelContext']>, ParentType, ContextType>;
  name?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  orgId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  organization?: Resolver<ResolversTypes['Organization'], ParentType, ContextType>;
  previewData?: Resolver<ResolversTypes['PreviewData'], ParentType, ContextType>;
  runs?: Resolver<ResolversTypes['RunConnection'], ParentType, ContextType, RequireFields<StaticModelRunsArgs, 'first'>>;
  updatedAt?: Resolver<ResolversTypes['DateTime'], ParentType, ContextType>;
  __isTypeOf?: IsTypeOfResolverFn<ParentType, ContextType>;
};

export type StaticModelConnectionResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['StaticModelConnection'] = ResolversParentTypes['StaticModelConnection']> = {
  edges?: Resolver<Array<ResolversTypes['StaticModelEdge']>, ParentType, ContextType>;
  pageInfo?: Resolver<ResolversTypes['PageInfo'], ParentType, ContextType>;
  totalCount?: Resolver<Maybe<ResolversTypes['Int']>, ParentType, ContextType>;
};

export type StaticModelDefinitionResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['StaticModelDefinition'] = ResolversParentTypes['StaticModelDefinition']> = {
  datasetId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  orgId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  staticModels?: Resolver<ResolversTypes['StaticModelConnection'], ParentType, ContextType, RequireFields<StaticModelDefinitionStaticModelsArgs, 'first'>>;
  __isTypeOf?: IsTypeOfResolverFn<ParentType, ContextType>;
};

export type StaticModelEdgeResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['StaticModelEdge'] = ResolversParentTypes['StaticModelEdge']> = {
  cursor?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  node?: Resolver<ResolversTypes['StaticModel'], ParentType, ContextType>;
};

export type StepResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['Step'] = ResolversParentTypes['Step']> = {
  displayName?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  finishedAt?: Resolver<Maybe<ResolversTypes['DateTime']>, ParentType, ContextType>;
  id?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  logsUrl?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  materializations?: Resolver<ResolversTypes['MaterializationConnection'], ParentType, ContextType>;
  name?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  run?: Resolver<ResolversTypes['Run'], ParentType, ContextType>;
  runId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  startedAt?: Resolver<ResolversTypes['DateTime'], ParentType, ContextType>;
  status?: Resolver<ResolversTypes['StepStatus'], ParentType, ContextType>;
};

export type StepConnectionResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['StepConnection'] = ResolversParentTypes['StepConnection']> = {
  edges?: Resolver<Array<ResolversTypes['StepEdge']>, ParentType, ContextType>;
  pageInfo?: Resolver<ResolversTypes['PageInfo'], ParentType, ContextType>;
  totalCount?: Resolver<Maybe<ResolversTypes['Int']>, ParentType, ContextType>;
};

export type StepEdgeResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['StepEdge'] = ResolversParentTypes['StepEdge']> = {
  cursor?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  node?: Resolver<ResolversTypes['Step'], ParentType, ContextType>;
};

export type SyncDataConnectionPayloadResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['SyncDataConnectionPayload'] = ResolversParentTypes['SyncDataConnectionPayload']> = {
  message?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  run?: Resolver<ResolversTypes['Run'], ParentType, ContextType>;
  success?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
};

export type SystemResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['System'] = ResolversParentTypes['System']> = {
  resolveTables?: Resolver<Array<ResolversTypes['SystemResolvedTableReference']>, ParentType, ContextType, RequireFields<SystemResolveTablesArgs, 'references'>>;
};

export type SystemResolvedTableReferenceResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['SystemResolvedTableReference'] = ResolversParentTypes['SystemResolvedTableReference']> = {
  fqn?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  reference?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
};

export type TableResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['Table'] = ResolversParentTypes['Table']> = {
  columns?: Resolver<Array<ResolversTypes['TableColumn']>, ParentType, ContextType>;
  dataset?: Resolver<ResolversTypes['Dataset'], ParentType, ContextType>;
  datasetId?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  id?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  name?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  source?: Resolver<ResolversTypes['TableSource'], ParentType, ContextType>;
};

export type TableColumnResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['TableColumn'] = ResolversParentTypes['TableColumn']> = {
  name?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  nullable?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
  type?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
};

export type TableConnectionResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['TableConnection'] = ResolversParentTypes['TableConnection']> = {
  edges?: Resolver<Array<ResolversTypes['TableEdge']>, ParentType, ContextType>;
  pageInfo?: Resolver<ResolversTypes['PageInfo'], ParentType, ContextType>;
  totalCount?: Resolver<Maybe<ResolversTypes['Int']>, ParentType, ContextType>;
};

export type TableEdgeResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['TableEdge'] = ResolversParentTypes['TableEdge']> = {
  cursor?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  node?: Resolver<ResolversTypes['Table'], ParentType, ContextType>;
};

export type TableSourceResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['TableSource'] = ResolversParentTypes['TableSource']> = {
  __resolveType: TypeResolveFn<'DataConnection' | 'DataIngestion' | 'DataModel' | 'StaticModel', ParentType, ContextType>;
};

export type UnpublishNotebookPayloadResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['UnpublishNotebookPayload'] = ResolversParentTypes['UnpublishNotebookPayload']> = {
  message?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  success?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
};

export type UpdateDatasetPayloadResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['UpdateDatasetPayload'] = ResolversParentTypes['UpdateDatasetPayload']> = {
  dataset?: Resolver<Maybe<ResolversTypes['Dataset']>, ParentType, ContextType>;
  message?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  success?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
};

export type UpdateMemberRolePayloadResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['UpdateMemberRolePayload'] = ResolversParentTypes['UpdateMemberRolePayload']> = {
  member?: Resolver<Maybe<ResolversTypes['OrganizationMember']>, ParentType, ContextType>;
  message?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  success?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
};

export type UpdateModelContextPayloadResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['UpdateModelContextPayload'] = ResolversParentTypes['UpdateModelContextPayload']> = {
  message?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  modelContext?: Resolver<Maybe<ResolversTypes['ModelContext']>, ParentType, ContextType>;
  success?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
};

export type UpdateNotebookPayloadResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['UpdateNotebookPayload'] = ResolversParentTypes['UpdateNotebookPayload']> = {
  message?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  notebook?: Resolver<Maybe<ResolversTypes['Notebook']>, ParentType, ContextType>;
  success?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
};

export type UpdateRunMetadataPayloadResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['UpdateRunMetadataPayload'] = ResolversParentTypes['UpdateRunMetadataPayload']> = {
  message?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  run?: Resolver<Maybe<ResolversTypes['Run']>, ParentType, ContextType>;
  success?: Resolver<ResolversTypes['Boolean'], ParentType, ContextType>;
};

export type UserResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['User'] = ResolversParentTypes['User']> = {
  avatarUrl?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  email?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  fullName?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  id?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  organizations?: Resolver<ResolversTypes['OrganizationConnection'], ParentType, ContextType, RequireFields<UserOrganizationsArgs, 'first'>>;
};

export type UserConnectionResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['UserConnection'] = ResolversParentTypes['UserConnection']> = {
  edges?: Resolver<Array<ResolversTypes['UserEdge']>, ParentType, ContextType>;
  pageInfo?: Resolver<ResolversTypes['PageInfo'], ParentType, ContextType>;
  totalCount?: Resolver<Maybe<ResolversTypes['Int']>, ParentType, ContextType>;
};

export type UserEdgeResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['UserEdge'] = ResolversParentTypes['UserEdge']> = {
  cursor?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  node?: Resolver<ResolversTypes['User'], ParentType, ContextType>;
};

export type ViewerResolvers<ContextType = GraphQLContext, ParentType extends ResolversParentTypes['Viewer'] = ResolversParentTypes['Viewer']> = {
  avatarUrl?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  datasets?: Resolver<ResolversTypes['DatasetConnection'], ParentType, ContextType, RequireFields<ViewerDatasetsArgs, 'first'>>;
  email?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  fullName?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  id?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  invitations?: Resolver<ResolversTypes['InvitationConnection'], ParentType, ContextType, RequireFields<ViewerInvitationsArgs, 'first'>>;
  notebooks?: Resolver<ResolversTypes['NotebookConnection'], ParentType, ContextType, RequireFields<ViewerNotebooksArgs, 'first'>>;
  organizations?: Resolver<ResolversTypes['OrganizationConnection'], ParentType, ContextType, RequireFields<ViewerOrganizationsArgs, 'first'>>;
  runs?: Resolver<ResolversTypes['RunConnection'], ParentType, ContextType, RequireFields<ViewerRunsArgs, 'first'>>;
};

export type Resolvers<ContextType = GraphQLContext> = {
  AcceptInvitationPayload?: AcceptInvitationPayloadResolvers<ContextType>;
  AddUserByEmailPayload?: AddUserByEmailPayloadResolvers<ContextType>;
  CancelRunPayload?: CancelRunPayloadResolvers<ContextType>;
  CreateDataConnectionPayload?: CreateDataConnectionPayloadResolvers<ContextType>;
  CreateDataModelPayload?: CreateDataModelPayloadResolvers<ContextType>;
  CreateDataModelReleasePayload?: CreateDataModelReleasePayloadResolvers<ContextType>;
  CreateDataModelRevisionPayload?: CreateDataModelRevisionPayloadResolvers<ContextType>;
  CreateDatasetPayload?: CreateDatasetPayloadResolvers<ContextType>;
  CreateInvitationPayload?: CreateInvitationPayloadResolvers<ContextType>;
  CreateMaterializationPayload?: CreateMaterializationPayloadResolvers<ContextType>;
  CreateNotebookPayload?: CreateNotebookPayloadResolvers<ContextType>;
  CreateRunRequestPayload?: CreateRunRequestPayloadResolvers<ContextType>;
  CreateStaticModelPayload?: CreateStaticModelPayloadResolvers<ContextType>;
  DataConnection?: DataConnectionResolvers<ContextType>;
  DataConnectionAlias?: DataConnectionAliasResolvers<ContextType>;
  DataConnectionConnection?: DataConnectionConnectionResolvers<ContextType>;
  DataConnectionDefinition?: DataConnectionDefinitionResolvers<ContextType>;
  DataConnectionEdge?: DataConnectionEdgeResolvers<ContextType>;
  DataConnectionSchema?: DataConnectionSchemaResolvers<ContextType>;
  DataConnectionTable?: DataConnectionTableResolvers<ContextType>;
  DataIngestion?: DataIngestionResolvers<ContextType>;
  DataIngestionConnection?: DataIngestionConnectionResolvers<ContextType>;
  DataIngestionDefinition?: DataIngestionDefinitionResolvers<ContextType>;
  DataIngestionEdge?: DataIngestionEdgeResolvers<ContextType>;
  DataModel?: DataModelResolvers<ContextType>;
  DataModelColumn?: DataModelColumnResolvers<ContextType>;
  DataModelConnection?: DataModelConnectionResolvers<ContextType>;
  DataModelDefinition?: DataModelDefinitionResolvers<ContextType>;
  DataModelDependency?: DataModelDependencyResolvers<ContextType>;
  DataModelEdge?: DataModelEdgeResolvers<ContextType>;
  DataModelKindOptions?: DataModelKindOptionsResolvers<ContextType>;
  DataModelRelease?: DataModelReleaseResolvers<ContextType>;
  DataModelReleaseConnection?: DataModelReleaseConnectionResolvers<ContextType>;
  DataModelReleaseEdge?: DataModelReleaseEdgeResolvers<ContextType>;
  DataModelRevision?: DataModelRevisionResolvers<ContextType>;
  DataModelRevisionConnection?: DataModelRevisionConnectionResolvers<ContextType>;
  DataModelRevisionEdge?: DataModelRevisionEdgeResolvers<ContextType>;
  Dataset?: DatasetResolvers<ContextType>;
  DatasetConnection?: DatasetConnectionResolvers<ContextType>;
  DatasetEdge?: DatasetEdgeResolvers<ContextType>;
  DatasetTypeDefinition?: DatasetTypeDefinitionResolvers<ContextType>;
  DateTime?: GraphQLScalarType;
  FinishRunPayload?: FinishRunPayloadResolvers<ContextType>;
  FinishStepPayload?: FinishStepPayloadResolvers<ContextType>;
  Invitation?: InvitationResolvers<ContextType>;
  InvitationConnection?: InvitationConnectionResolvers<ContextType>;
  InvitationEdge?: InvitationEdgeResolvers<ContextType>;
  JSON?: GraphQLScalarType;
  Materialization?: MaterializationResolvers<ContextType>;
  MaterializationConnection?: MaterializationConnectionResolvers<ContextType>;
  MaterializationEdge?: MaterializationEdgeResolvers<ContextType>;
  ModelColumnContext?: ModelColumnContextResolvers<ContextType>;
  ModelContext?: ModelContextResolvers<ContextType>;
  Mutation?: MutationResolvers<ContextType>;
  Notebook?: NotebookResolvers<ContextType>;
  NotebookConnection?: NotebookConnectionResolvers<ContextType>;
  NotebookEdge?: NotebookEdgeResolvers<ContextType>;
  Organization?: OrganizationResolvers<ContextType>;
  OrganizationConnection?: OrganizationConnectionResolvers<ContextType>;
  OrganizationEdge?: OrganizationEdgeResolvers<ContextType>;
  OrganizationMember?: OrganizationMemberResolvers<ContextType>;
  PageInfo?: PageInfoResolvers<ContextType>;
  PreviewData?: PreviewDataResolvers<ContextType>;
  PublishNotebookPayload?: PublishNotebookPayloadResolvers<ContextType>;
  Query?: QueryResolvers<ContextType>;
  RemoveMemberPayload?: RemoveMemberPayloadResolvers<ContextType>;
  RevokeInvitationPayload?: RevokeInvitationPayloadResolvers<ContextType>;
  Run?: RunResolvers<ContextType>;
  RunConnection?: RunConnectionResolvers<ContextType>;
  RunEdge?: RunEdgeResolvers<ContextType>;
  SaveNotebookPreviewPayload?: SaveNotebookPreviewPayloadResolvers<ContextType>;
  SavePublishedNotebookHtmlPayload?: SavePublishedNotebookHtmlPayloadResolvers<ContextType>;
  SimplePayload?: SimplePayloadResolvers<ContextType>;
  StartRunPayload?: StartRunPayloadResolvers<ContextType>;
  StartStepPayload?: StartStepPayloadResolvers<ContextType>;
  StaticModel?: StaticModelResolvers<ContextType>;
  StaticModelConnection?: StaticModelConnectionResolvers<ContextType>;
  StaticModelDefinition?: StaticModelDefinitionResolvers<ContextType>;
  StaticModelEdge?: StaticModelEdgeResolvers<ContextType>;
  Step?: StepResolvers<ContextType>;
  StepConnection?: StepConnectionResolvers<ContextType>;
  StepEdge?: StepEdgeResolvers<ContextType>;
  SyncDataConnectionPayload?: SyncDataConnectionPayloadResolvers<ContextType>;
  System?: SystemResolvers<ContextType>;
  SystemResolvedTableReference?: SystemResolvedTableReferenceResolvers<ContextType>;
  Table?: TableResolvers<ContextType>;
  TableColumn?: TableColumnResolvers<ContextType>;
  TableConnection?: TableConnectionResolvers<ContextType>;
  TableEdge?: TableEdgeResolvers<ContextType>;
  TableSource?: TableSourceResolvers<ContextType>;
  UnpublishNotebookPayload?: UnpublishNotebookPayloadResolvers<ContextType>;
  UpdateDatasetPayload?: UpdateDatasetPayloadResolvers<ContextType>;
  UpdateMemberRolePayload?: UpdateMemberRolePayloadResolvers<ContextType>;
  UpdateModelContextPayload?: UpdateModelContextPayloadResolvers<ContextType>;
  UpdateNotebookPayload?: UpdateNotebookPayloadResolvers<ContextType>;
  UpdateRunMetadataPayload?: UpdateRunMetadataPayloadResolvers<ContextType>;
  User?: UserResolvers<ContextType>;
  UserConnection?: UserConnectionResolvers<ContextType>;
  UserEdge?: UserEdgeResolvers<ContextType>;
  Viewer?: ViewerResolvers<ContextType>;
};

