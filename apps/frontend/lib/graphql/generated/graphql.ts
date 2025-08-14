/* eslint-disable */
import { TypedDocumentNode as DocumentNode } from "@graphql-typed-document-node/core";
export type Maybe<T> = T | null;
export type InputMaybe<T> = Maybe<T>;
export type Exact<T extends { [key: string]: unknown }> = {
  [K in keyof T]: T[K];
};
export type MakeOptional<T, K extends keyof T> = Omit<T, K> & {
  [SubKey in K]?: Maybe<T[SubKey]>;
};
export type MakeMaybe<T, K extends keyof T> = Omit<T, K> & {
  [SubKey in K]: Maybe<T[SubKey]>;
};
export type MakeEmpty<
  T extends { [key: string]: unknown },
  K extends keyof T,
> = { [_ in K]?: never };
export type Incremental<T> =
  | T
  | {
      [P in keyof T]?: P extends " $fragmentName" | "__typename" ? T[P] : never;
    };
/** All built-in and custom scalars, mapped to their actual values */
export type Scalars = {
  ID: { input: string; output: string };
  String: { input: string; output: string };
  Boolean: { input: boolean; output: boolean };
  Int: { input: number; output: number };
  Float: { input: number; output: number };
  /**
   * The `GenericScalar` scalar type represents a generic
   * GraphQL scalar value that could be:
   * String, Boolean, Int, Float, List or Object.
   */
  GenericScalar: { input: any; output: any };
  Oso_Bool: { input: any; output: any };
  Oso_Date: { input: any; output: any };
  Oso_DateTime: { input: any; output: any };
  Oso_DateTime646: { input: any; output: any };
  Oso_Float32: { input: any; output: any };
  Oso_Float64: { input: any; output: any };
  Oso_Int64: { input: any; output: any };
  /**
   * This type is used when passing in a configuration object
   *         for pipeline configuration. Can either be passed in as a string (the
   *         YAML configuration object) or as the configuration object itself. In
   *         either case, the object must conform to the constraints of the dagster config type system.
   *
   */
  RunConfigData: { input: any; output: any };
};

export type AddDynamicPartitionResult =
  | AddDynamicPartitionSuccess
  | DuplicateDynamicPartitionError
  | PythonError
  | UnauthorizedError;

export type AddDynamicPartitionSuccess = {
  __typename?: "AddDynamicPartitionSuccess";
  partitionKey: Scalars["String"]["output"];
  partitionsDefName: Scalars["String"]["output"];
};

export type AlertFailureEvent = MessageEvent &
  RunEvent & {
    __typename?: "AlertFailureEvent";
    eventType?: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars["String"]["output"];
    pipelineName: Scalars["String"]["output"];
    runId: Scalars["String"]["output"];
    solidHandleID?: Maybe<Scalars["String"]["output"]>;
    stepKey?: Maybe<Scalars["String"]["output"]>;
    timestamp: Scalars["String"]["output"];
  };

export type AlertStartEvent = MessageEvent &
  RunEvent & {
    __typename?: "AlertStartEvent";
    eventType?: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars["String"]["output"];
    pipelineName: Scalars["String"]["output"];
    runId: Scalars["String"]["output"];
    solidHandleID?: Maybe<Scalars["String"]["output"]>;
    stepKey?: Maybe<Scalars["String"]["output"]>;
    timestamp: Scalars["String"]["output"];
  };

export type AlertSuccessEvent = MessageEvent &
  RunEvent & {
    __typename?: "AlertSuccessEvent";
    eventType?: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars["String"]["output"];
    pipelineName: Scalars["String"]["output"];
    runId: Scalars["String"]["output"];
    solidHandleID?: Maybe<Scalars["String"]["output"]>;
    stepKey?: Maybe<Scalars["String"]["output"]>;
    timestamp: Scalars["String"]["output"];
  };

export type ArrayConfigType = ConfigType &
  WrappingConfigType & {
    __typename?: "ArrayConfigType";
    description?: Maybe<Scalars["String"]["output"]>;
    isSelector: Scalars["Boolean"]["output"];
    key: Scalars["String"]["output"];
    ofType: ConfigType;
    /**
     *
     * This is an odd and problematic field. It recursively goes down to
     * get all the types contained within a type. The case where it is horrible
     * are dictionaries and it recurses all the way down to the leaves. This means
     * that in a case where one is fetching all the types and then all the inner
     * types keys for those types, we are returning O(N^2) type keys, which
     * can cause awful performance for large schemas. When you have access
     * to *all* the types, you should instead only use the type_param_keys
     * field for closed generic types and manually navigate down the to
     * field types client-side.
     *
     * Where it is useful is when you are fetching types independently and
     * want to be able to render them, but without fetching the entire schema.
     *
     * We use this capability when rendering the sidebar.
     *
     */
    recursiveConfigTypes: Array<ConfigType>;
    /**
     *
     * This returns the keys for type parameters of any closed generic type,
     * (e.g. List, Optional). This should be used for reconstructing and
     * navigating the full schema client-side and not innerTypes.
     *
     */
    typeParamKeys: Array<Scalars["String"]["output"]>;
  };

export type Asset = {
  __typename?: "Asset";
  assetMaterializations: Array<MaterializationEvent>;
  assetObservations: Array<ObservationEvent>;
  definition?: Maybe<AssetNode>;
  id: Scalars["String"]["output"];
  key: AssetKey;
};

export type AssetAssetMaterializationsArgs = {
  afterTimestampMillis?: InputMaybe<Scalars["String"]["input"]>;
  beforeTimestampMillis?: InputMaybe<Scalars["String"]["input"]>;
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  partitionInLast?: InputMaybe<Scalars["Int"]["input"]>;
  partitions?: InputMaybe<Array<Scalars["String"]["input"]>>;
};

export type AssetAssetObservationsArgs = {
  afterTimestampMillis?: InputMaybe<Scalars["String"]["input"]>;
  beforeTimestampMillis?: InputMaybe<Scalars["String"]["input"]>;
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  partitionInLast?: InputMaybe<Scalars["Int"]["input"]>;
  partitions?: InputMaybe<Array<Scalars["String"]["input"]>>;
};

export type AssetBackfillData = {
  __typename?: "AssetBackfillData";
  assetBackfillStatuses: Array<AssetBackfillStatus>;
  rootTargetedPartitions?: Maybe<AssetBackfillTargetPartitions>;
};

export type AssetBackfillPreviewParams = {
  assetSelection: Array<AssetKeyInput>;
  partitionNames: Array<Scalars["String"]["input"]>;
};

export type AssetBackfillStatus =
  | AssetPartitionsStatusCounts
  | UnpartitionedAssetStatus;

export type AssetBackfillTargetPartitions = {
  __typename?: "AssetBackfillTargetPartitions";
  partitionKeys?: Maybe<Array<Scalars["String"]["output"]>>;
  ranges?: Maybe<Array<PartitionKeyRange>>;
};

export type AssetCheck = {
  __typename?: "AssetCheck";
  additionalAssetKeys: Array<AssetKey>;
  assetKey: AssetKey;
  automationCondition?: Maybe<AutomationCondition>;
  blocking: Scalars["Boolean"]["output"];
  canExecuteIndividually: AssetCheckCanExecuteIndividually;
  description?: Maybe<Scalars["String"]["output"]>;
  executionForLatestMaterialization?: Maybe<AssetCheckExecution>;
  jobNames: Array<Scalars["String"]["output"]>;
  name: Scalars["String"]["output"];
};

export enum AssetCheckCanExecuteIndividually {
  CanExecute = "CAN_EXECUTE",
  NeedsUserCodeUpgrade = "NEEDS_USER_CODE_UPGRADE",
  RequiresMaterialization = "REQUIRES_MATERIALIZATION",
}

export type AssetCheckEvaluation = {
  __typename?: "AssetCheckEvaluation";
  assetKey: AssetKey;
  checkName: Scalars["String"]["output"];
  description?: Maybe<Scalars["String"]["output"]>;
  metadataEntries: Array<MetadataEntry>;
  severity: AssetCheckSeverity;
  success: Scalars["Boolean"]["output"];
  targetMaterialization?: Maybe<AssetCheckEvaluationTargetMaterializationData>;
  /** When the check evaluation was stored */
  timestamp: Scalars["Float"]["output"];
};

export type AssetCheckEvaluationEvent = MessageEvent &
  StepEvent & {
    __typename?: "AssetCheckEvaluationEvent";
    evaluation: AssetCheckEvaluation;
    eventType?: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars["String"]["output"];
    runId: Scalars["String"]["output"];
    solidHandleID?: Maybe<Scalars["String"]["output"]>;
    stepKey?: Maybe<Scalars["String"]["output"]>;
    timestamp: Scalars["String"]["output"];
  };

export type AssetCheckEvaluationPlannedEvent = MessageEvent &
  StepEvent & {
    __typename?: "AssetCheckEvaluationPlannedEvent";
    assetKey: AssetKey;
    checkName: Scalars["String"]["output"];
    eventType?: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars["String"]["output"];
    runId: Scalars["String"]["output"];
    solidHandleID?: Maybe<Scalars["String"]["output"]>;
    stepKey?: Maybe<Scalars["String"]["output"]>;
    timestamp: Scalars["String"]["output"];
  };

export type AssetCheckEvaluationTargetMaterializationData = {
  __typename?: "AssetCheckEvaluationTargetMaterializationData";
  runId: Scalars["String"]["output"];
  storageId: Scalars["ID"]["output"];
  timestamp: Scalars["Float"]["output"];
};

export type AssetCheckExecution = {
  __typename?: "AssetCheckExecution";
  evaluation?: Maybe<AssetCheckEvaluation>;
  id: Scalars["String"]["output"];
  runId: Scalars["String"]["output"];
  status: AssetCheckExecutionResolvedStatus;
  stepKey?: Maybe<Scalars["String"]["output"]>;
  /** When the check run started */
  timestamp: Scalars["Float"]["output"];
};

/** An enumeration. */
export enum AssetCheckExecutionResolvedStatus {
  ExecutionFailed = "EXECUTION_FAILED",
  Failed = "FAILED",
  InProgress = "IN_PROGRESS",
  Skipped = "SKIPPED",
  Succeeded = "SUCCEEDED",
}

export type AssetCheckHandleInput = {
  assetKey: AssetKeyInput;
  name: Scalars["String"]["input"];
};

export type AssetCheckNeedsAgentUpgradeError = Error & {
  __typename?: "AssetCheckNeedsAgentUpgradeError";
  message: Scalars["String"]["output"];
};

export type AssetCheckNeedsMigrationError = Error & {
  __typename?: "AssetCheckNeedsMigrationError";
  message: Scalars["String"]["output"];
};

export type AssetCheckNeedsUserCodeUpgrade = Error & {
  __typename?: "AssetCheckNeedsUserCodeUpgrade";
  message: Scalars["String"]["output"];
};

/**
 * Severity level for an AssetCheckResult.
 *
 *     - WARN: a potential issue with the asset
 *     - ERROR: a definite issue with the asset
 *
 *     Severity does not impact execution of the asset or downstream assets.
 *
 */
export enum AssetCheckSeverity {
  Error = "ERROR",
  Warn = "WARN",
}

export type AssetCheckhandle = {
  __typename?: "AssetCheckhandle";
  assetKey: AssetKey;
  name: Scalars["String"]["output"];
};

export type AssetChecks = {
  __typename?: "AssetChecks";
  checks: Array<AssetCheck>;
};

export type AssetChecksOrError =
  | AssetCheckNeedsAgentUpgradeError
  | AssetCheckNeedsMigrationError
  | AssetCheckNeedsUserCodeUpgrade
  | AssetChecks;

export type AssetConditionEvaluation = {
  __typename?: "AssetConditionEvaluation";
  evaluationNodes: Array<AssetConditionEvaluationNode>;
  rootUniqueId: Scalars["String"]["output"];
};

export type AssetConditionEvaluationNode =
  | PartitionedAssetConditionEvaluationNode
  | SpecificPartitionAssetConditionEvaluationNode
  | UnpartitionedAssetConditionEvaluationNode;

export type AssetConditionEvaluationRecord = {
  __typename?: "AssetConditionEvaluationRecord";
  assetKey?: Maybe<AssetKey>;
  endTimestamp?: Maybe<Scalars["Float"]["output"]>;
  entityKey: EntityKey;
  evaluation: AssetConditionEvaluation;
  evaluationId: Scalars["ID"]["output"];
  evaluationNodes: Array<AutomationConditionEvaluationNode>;
  id: Scalars["ID"]["output"];
  isLegacy: Scalars["Boolean"]["output"];
  numRequested: Scalars["Int"]["output"];
  rootUniqueId: Scalars["String"]["output"];
  runIds: Array<Scalars["String"]["output"]>;
  startTimestamp?: Maybe<Scalars["Float"]["output"]>;
  timestamp: Scalars["Float"]["output"];
};

export type AssetConditionEvaluationRecords = {
  __typename?: "AssetConditionEvaluationRecords";
  records: Array<AssetConditionEvaluationRecord>;
};

export type AssetConditionEvaluationRecordsOrError =
  | AssetConditionEvaluationRecords
  | AutoMaterializeAssetEvaluationNeedsMigrationError;

/** An enumeration. */
export enum AssetConditionEvaluationStatus {
  False = "FALSE",
  Skipped = "SKIPPED",
  True = "TRUE",
}

export type AssetConnection = {
  __typename?: "AssetConnection";
  cursor?: Maybe<Scalars["String"]["output"]>;
  nodes: Array<Asset>;
};

export type AssetDependency = {
  __typename?: "AssetDependency";
  asset: AssetNode;
  partitionMapping?: Maybe<PartitionMapping>;
};

/** The event type of an asset event. */
export enum AssetEventType {
  AssetMaterialization = "ASSET_MATERIALIZATION",
  AssetObservation = "ASSET_OBSERVATION",
}

export type AssetFreshnessInfo = {
  __typename?: "AssetFreshnessInfo";
  currentLagMinutes?: Maybe<Scalars["Float"]["output"]>;
  currentMinutesLate?: Maybe<Scalars["Float"]["output"]>;
  latestMaterializationMinutesLate?: Maybe<Scalars["Float"]["output"]>;
};

export type AssetGroup = {
  __typename?: "AssetGroup";
  assetKeys: Array<AssetKey>;
  groupName: Scalars["String"]["output"];
  id: Scalars["String"]["output"];
};

/**
 * This type represents the fields necessary to identify
 *         an asset group.
 */
export type AssetGroupSelector = {
  groupName: Scalars["String"]["input"];
  repositoryLocationName: Scalars["String"]["input"];
  repositoryName: Scalars["String"]["input"];
};

export type AssetKey = {
  __typename?: "AssetKey";
  path: Array<Scalars["String"]["output"]>;
};

export type AssetKeyInput = {
  path: Array<Scalars["String"]["input"]>;
};

export type AssetLatestInfo = {
  __typename?: "AssetLatestInfo";
  assetKey: AssetKey;
  id: Scalars["ID"]["output"];
  inProgressRunIds: Array<Scalars["String"]["output"]>;
  latestMaterialization?: Maybe<MaterializationEvent>;
  latestRun?: Maybe<Run>;
  unstartedRunIds: Array<Scalars["String"]["output"]>;
};

export type AssetLineageInfo = {
  __typename?: "AssetLineageInfo";
  assetKey: AssetKey;
  partitions: Array<Scalars["String"]["output"]>;
};

export type AssetMaterializationPlannedEvent = MessageEvent &
  RunEvent & {
    __typename?: "AssetMaterializationPlannedEvent";
    assetKey?: Maybe<AssetKey>;
    eventType?: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars["String"]["output"];
    pipelineName: Scalars["String"]["output"];
    runId: Scalars["String"]["output"];
    runOrError: RunOrError;
    solidHandleID?: Maybe<Scalars["String"]["output"]>;
    stepKey?: Maybe<Scalars["String"]["output"]>;
    timestamp: Scalars["String"]["output"];
  };

export type AssetMetadataEntry = MetadataEntry & {
  __typename?: "AssetMetadataEntry";
  assetKey: AssetKey;
  description?: Maybe<Scalars["String"]["output"]>;
  label: Scalars["String"]["output"];
};

export type AssetNode = {
  __typename?: "AssetNode";
  assetChecksOrError: AssetChecksOrError;
  assetKey: AssetKey;
  assetMaterializationUsedData: Array<MaterializationUpstreamDataVersion>;
  assetMaterializations: Array<MaterializationEvent>;
  assetObservations: Array<ObservationEvent>;
  assetPartitionStatuses: AssetPartitionStatuses;
  autoMaterializePolicy?: Maybe<AutoMaterializePolicy>;
  automationCondition?: Maybe<AutomationCondition>;
  backfillPolicy?: Maybe<BackfillPolicy>;
  changedReasons: Array<ChangeReason>;
  computeKind?: Maybe<Scalars["String"]["output"]>;
  configField?: Maybe<ConfigTypeField>;
  currentAutoMaterializeEvaluationId?: Maybe<Scalars["ID"]["output"]>;
  dataVersion?: Maybe<Scalars["String"]["output"]>;
  dataVersionByPartition: Array<Maybe<Scalars["String"]["output"]>>;
  dependedBy: Array<AssetDependency>;
  dependedByKeys: Array<AssetKey>;
  dependencies: Array<AssetDependency>;
  dependencyKeys: Array<AssetKey>;
  description?: Maybe<Scalars["String"]["output"]>;
  freshnessInfo?: Maybe<AssetFreshnessInfo>;
  freshnessPolicy?: Maybe<FreshnessPolicy>;
  graphName?: Maybe<Scalars["String"]["output"]>;
  groupName: Scalars["String"]["output"];
  hasAssetChecks: Scalars["Boolean"]["output"];
  hasMaterializePermission: Scalars["Boolean"]["output"];
  hasReportRunlessAssetEventPermission: Scalars["Boolean"]["output"];
  id: Scalars["ID"]["output"];
  isExecutable: Scalars["Boolean"]["output"];
  isMaterializable: Scalars["Boolean"]["output"];
  isObservable: Scalars["Boolean"]["output"];
  isPartitioned: Scalars["Boolean"]["output"];
  jobNames: Array<Scalars["String"]["output"]>;
  jobs: Array<Pipeline>;
  kinds: Array<Scalars["String"]["output"]>;
  latestMaterializationByPartition: Array<Maybe<MaterializationEvent>>;
  latestRunForPartition?: Maybe<Run>;
  metadataEntries: Array<MetadataEntry>;
  op?: Maybe<SolidDefinition>;
  opName?: Maybe<Scalars["String"]["output"]>;
  opNames: Array<Scalars["String"]["output"]>;
  opVersion?: Maybe<Scalars["String"]["output"]>;
  owners: Array<AssetOwner>;
  partitionDefinition?: Maybe<PartitionDefinition>;
  partitionKeys: Array<Scalars["String"]["output"]>;
  partitionKeysByDimension: Array<DimensionPartitionKeys>;
  partitionStats?: Maybe<PartitionStats>;
  pools: Array<Scalars["String"]["output"]>;
  repository: Repository;
  requiredResources: Array<ResourceRequirement>;
  staleCauses: Array<StaleCause>;
  staleCausesByPartition?: Maybe<Array<Array<StaleCause>>>;
  staleStatus?: Maybe<StaleStatus>;
  staleStatusByPartition: Array<StaleStatus>;
  tags: Array<DefinitionTag>;
  targetingInstigators: Array<Instigator>;
  type?: Maybe<DagsterType>;
};

export type AssetNodeAssetChecksOrErrorArgs = {
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  pipeline?: InputMaybe<PipelineSelector>;
};

export type AssetNodeAssetMaterializationUsedDataArgs = {
  timestampMillis: Scalars["String"]["input"];
};

export type AssetNodeAssetMaterializationsArgs = {
  beforeTimestampMillis?: InputMaybe<Scalars["String"]["input"]>;
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  partitions?: InputMaybe<Array<Scalars["String"]["input"]>>;
};

export type AssetNodeAssetObservationsArgs = {
  beforeTimestampMillis?: InputMaybe<Scalars["String"]["input"]>;
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  partitions?: InputMaybe<Array<Scalars["String"]["input"]>>;
};

export type AssetNodeDataVersionArgs = {
  partition?: InputMaybe<Scalars["String"]["input"]>;
};

export type AssetNodeDataVersionByPartitionArgs = {
  partitions?: InputMaybe<Array<Scalars["String"]["input"]>>;
};

export type AssetNodeLatestMaterializationByPartitionArgs = {
  partitions?: InputMaybe<Array<Scalars["String"]["input"]>>;
};

export type AssetNodeLatestRunForPartitionArgs = {
  partition: Scalars["String"]["input"];
};

export type AssetNodePartitionKeysByDimensionArgs = {
  endIdx?: InputMaybe<Scalars["Int"]["input"]>;
  startIdx?: InputMaybe<Scalars["Int"]["input"]>;
};

export type AssetNodeStaleCausesArgs = {
  partition?: InputMaybe<Scalars["String"]["input"]>;
};

export type AssetNodeStaleCausesByPartitionArgs = {
  partitions?: InputMaybe<Array<Scalars["String"]["input"]>>;
};

export type AssetNodeStaleStatusArgs = {
  partition?: InputMaybe<Scalars["String"]["input"]>;
};

export type AssetNodeStaleStatusByPartitionArgs = {
  partitions?: InputMaybe<Array<Scalars["String"]["input"]>>;
};

export type AssetNodeDefinitionCollision = {
  __typename?: "AssetNodeDefinitionCollision";
  assetKey: AssetKey;
  repositories: Array<Repository>;
};

export type AssetNodeOrError = AssetNode | AssetNotFoundError;

export type AssetNotFoundError = Error & {
  __typename?: "AssetNotFoundError";
  message: Scalars["String"]["output"];
};

export type AssetOrError = Asset | AssetNotFoundError;

export type AssetOwner = TeamAssetOwner | UserAssetOwner;

export type AssetPartitionRange = {
  __typename?: "AssetPartitionRange";
  assetKey: AssetKey;
  partitionRange?: Maybe<PartitionRange>;
};

export type AssetPartitionStatuses =
  | DefaultPartitionStatuses
  | MultiPartitionStatuses
  | TimePartitionStatuses;

export type AssetPartitions = {
  __typename?: "AssetPartitions";
  assetKey: AssetKey;
  partitions?: Maybe<AssetBackfillTargetPartitions>;
};

export type AssetPartitionsStatusCounts = {
  __typename?: "AssetPartitionsStatusCounts";
  assetKey: AssetKey;
  numPartitionsFailed: Scalars["Int"]["output"];
  numPartitionsInProgress: Scalars["Int"]["output"];
  numPartitionsMaterialized: Scalars["Int"]["output"];
  numPartitionsTargeted: Scalars["Int"]["output"];
};

export type AssetSelection = {
  __typename?: "AssetSelection";
  assetChecks: Array<AssetCheckhandle>;
  assetKeys: Array<AssetKey>;
  assetSelectionString?: Maybe<Scalars["String"]["output"]>;
  assets: Array<Asset>;
  assetsOrError: AssetsOrError;
};

/** The output from deleting asset history. */
export type AssetWipeMutationResult =
  | AssetNotFoundError
  | AssetWipeSuccess
  | PythonError
  | UnauthorizedError
  | UnsupportedOperationError;

/** Output indicating that asset history was deleted. */
export type AssetWipeSuccess = {
  __typename?: "AssetWipeSuccess";
  assetPartitionRanges: Array<AssetPartitionRange>;
};

export type AssetsOrError = AssetConnection | PythonError;

export type AutoMaterializeAssetEvaluationNeedsMigrationError = Error & {
  __typename?: "AutoMaterializeAssetEvaluationNeedsMigrationError";
  message: Scalars["String"]["output"];
};

export type AutoMaterializeAssetEvaluationRecord = {
  __typename?: "AutoMaterializeAssetEvaluationRecord";
  assetKey: AssetKey;
  evaluationId: Scalars["ID"]["output"];
  id: Scalars["ID"]["output"];
  numDiscarded: Scalars["Int"]["output"];
  numRequested: Scalars["Int"]["output"];
  numSkipped: Scalars["Int"]["output"];
  rules?: Maybe<Array<AutoMaterializeRule>>;
  rulesWithRuleEvaluations: Array<AutoMaterializeRuleWithRuleEvaluations>;
  runIds: Array<Scalars["String"]["output"]>;
  timestamp: Scalars["Float"]["output"];
};

export type AutoMaterializeAssetEvaluationRecords = {
  __typename?: "AutoMaterializeAssetEvaluationRecords";
  records: Array<AutoMaterializeAssetEvaluationRecord>;
};

export type AutoMaterializeAssetEvaluationRecordsOrError =
  | AutoMaterializeAssetEvaluationNeedsMigrationError
  | AutoMaterializeAssetEvaluationRecords;

/**
 * Represents the set of results of the auto-materialize logic.
 *
 *     MATERIALIZE: The asset should be materialized by a run kicked off on this tick
 *     SKIP: The asset should not be materialized by a run kicked off on this tick, because future
 *         ticks are expected to materialize it.
 *     DISCARD: The asset should not be materialized by a run kicked off on this tick, but future
 *         ticks are not expected to materialize it.
 *
 */
export enum AutoMaterializeDecisionType {
  Discard = "DISCARD",
  Materialize = "MATERIALIZE",
  Skip = "SKIP",
}

export type AutoMaterializePolicy = {
  __typename?: "AutoMaterializePolicy";
  maxMaterializationsPerMinute?: Maybe<Scalars["Int"]["output"]>;
  policyType: AutoMaterializePolicyType;
  rules: Array<AutoMaterializeRule>;
};

/** An enumeration. */
export enum AutoMaterializePolicyType {
  Eager = "EAGER",
  Lazy = "LAZY",
}

export type AutoMaterializeRule = {
  __typename?: "AutoMaterializeRule";
  className: Scalars["String"]["output"];
  decisionType: AutoMaterializeDecisionType;
  description: Scalars["String"]["output"];
};

export type AutoMaterializeRuleEvaluation = {
  __typename?: "AutoMaterializeRuleEvaluation";
  evaluationData?: Maybe<AutoMaterializeRuleEvaluationData>;
  partitionKeysOrError?: Maybe<PartitionKeysOrError>;
};

export type AutoMaterializeRuleEvaluationData =
  | ParentMaterializedRuleEvaluationData
  | TextRuleEvaluationData
  | WaitingOnKeysRuleEvaluationData;

export type AutoMaterializeRuleWithRuleEvaluations = {
  __typename?: "AutoMaterializeRuleWithRuleEvaluations";
  rule: AutoMaterializeRule;
  ruleEvaluations: Array<AutoMaterializeRuleEvaluation>;
};

export type AutomationCondition = {
  __typename?: "AutomationCondition";
  expandedLabel: Array<Scalars["String"]["output"]>;
  label?: Maybe<Scalars["String"]["output"]>;
};

export type AutomationConditionEvaluationNode = {
  __typename?: "AutomationConditionEvaluationNode";
  childUniqueIds: Array<Scalars["String"]["output"]>;
  endTimestamp?: Maybe<Scalars["Float"]["output"]>;
  expandedLabel: Array<Scalars["String"]["output"]>;
  isPartitioned: Scalars["Boolean"]["output"];
  numCandidates?: Maybe<Scalars["Int"]["output"]>;
  numTrue: Scalars["Int"]["output"];
  startTimestamp?: Maybe<Scalars["Float"]["output"]>;
  uniqueId: Scalars["String"]["output"];
  userLabel?: Maybe<Scalars["String"]["output"]>;
};

export type BackfillNotFoundError = Error & {
  __typename?: "BackfillNotFoundError";
  backfillId: Scalars["String"]["output"];
  message: Scalars["String"]["output"];
};

export type BackfillPolicy = {
  __typename?: "BackfillPolicy";
  description: Scalars["String"]["output"];
  maxPartitionsPerRun?: Maybe<Scalars["Int"]["output"]>;
  policyType: BackfillPolicyType;
};

/** An enumeration. */
export enum BackfillPolicyType {
  MultiRun = "MULTI_RUN",
  SingleRun = "SINGLE_RUN",
}

export type BoolMetadataEntry = MetadataEntry & {
  __typename?: "BoolMetadataEntry";
  boolValue?: Maybe<Scalars["Boolean"]["output"]>;
  description?: Maybe<Scalars["String"]["output"]>;
  label: Scalars["String"]["output"];
};

export enum BulkActionStatus {
  Canceled = "CANCELED",
  Canceling = "CANCELING",
  Completed = "COMPLETED",
  CompletedFailed = "COMPLETED_FAILED",
  CompletedSuccess = "COMPLETED_SUCCESS",
  Failed = "FAILED",
  Requested = "REQUESTED",
}

/** This type represents a filter on Dagster Bulk Actions (backfills). */
export type BulkActionsFilter = {
  createdAfter?: InputMaybe<Scalars["Float"]["input"]>;
  createdBefore?: InputMaybe<Scalars["Float"]["input"]>;
  statuses?: InputMaybe<Array<BulkActionStatus>>;
};

export type CancelBackfillResult =
  | CancelBackfillSuccess
  | PythonError
  | UnauthorizedError;

export type CancelBackfillSuccess = {
  __typename?: "CancelBackfillSuccess";
  backfillId: Scalars["String"]["output"];
};

export type CapturedLogs = {
  __typename?: "CapturedLogs";
  cursor?: Maybe<Scalars["String"]["output"]>;
  logKey: Array<Scalars["String"]["output"]>;
  stderr?: Maybe<Scalars["String"]["output"]>;
  stdout?: Maybe<Scalars["String"]["output"]>;
};

export type CapturedLogsMetadata = {
  __typename?: "CapturedLogsMetadata";
  stderrDownloadUrl?: Maybe<Scalars["String"]["output"]>;
  stderrLocation?: Maybe<Scalars["String"]["output"]>;
  stdoutDownloadUrl?: Maybe<Scalars["String"]["output"]>;
  stdoutLocation?: Maybe<Scalars["String"]["output"]>;
};

/**
 * What change an asset has undergone between two deployments. Used
 *     in distinguishing asset definition changes in branch deployment and
 *     in subsequent other deployments.
 *
 */
export enum ChangeReason {
  CodeVersion = "CODE_VERSION",
  Dependencies = "DEPENDENCIES",
  Metadata = "METADATA",
  New = "NEW",
  PartitionsDefinition = "PARTITIONS_DEFINITION",
  Removed = "REMOVED",
  Tags = "TAGS",
}

export type ClaimedConcurrencySlot = {
  __typename?: "ClaimedConcurrencySlot";
  runId: Scalars["String"]["output"];
  stepKey: Scalars["String"]["output"];
};

export type CodeReferencesMetadataEntry = MetadataEntry & {
  __typename?: "CodeReferencesMetadataEntry";
  codeReferences: Array<SourceLocation>;
  description?: Maybe<Scalars["String"]["output"]>;
  label: Scalars["String"]["output"];
};

export type CompositeConfigType = ConfigType & {
  __typename?: "CompositeConfigType";
  description?: Maybe<Scalars["String"]["output"]>;
  fields: Array<ConfigTypeField>;
  isSelector: Scalars["Boolean"]["output"];
  key: Scalars["String"]["output"];
  /**
   *
   * This is an odd and problematic field. It recursively goes down to
   * get all the types contained within a type. The case where it is horrible
   * are dictionaries and it recurses all the way down to the leaves. This means
   * that in a case where one is fetching all the types and then all the inner
   * types keys for those types, we are returning O(N^2) type keys, which
   * can cause awful performance for large schemas. When you have access
   * to *all* the types, you should instead only use the type_param_keys
   * field for closed generic types and manually navigate down the to
   * field types client-side.
   *
   * Where it is useful is when you are fetching types independently and
   * want to be able to render them, but without fetching the entire schema.
   *
   * We use this capability when rendering the sidebar.
   *
   */
  recursiveConfigTypes: Array<ConfigType>;
  /**
   *
   * This returns the keys for type parameters of any closed generic type,
   * (e.g. List, Optional). This should be used for reconstructing and
   * navigating the full schema client-side and not innerTypes.
   *
   */
  typeParamKeys: Array<Scalars["String"]["output"]>;
};

export type CompositeSolidDefinition = ISolidDefinition &
  SolidContainer & {
    __typename?: "CompositeSolidDefinition";
    assetNodes: Array<AssetNode>;
    description?: Maybe<Scalars["String"]["output"]>;
    id: Scalars["ID"]["output"];
    inputDefinitions: Array<InputDefinition>;
    inputMappings: Array<InputMapping>;
    metadata: Array<MetadataItemDefinition>;
    modes: Array<Mode>;
    name: Scalars["String"]["output"];
    outputDefinitions: Array<OutputDefinition>;
    outputMappings: Array<OutputMapping>;
    pools: Array<Scalars["String"]["output"]>;
    solidHandle?: Maybe<SolidHandle>;
    solidHandles: Array<SolidHandle>;
    solids: Array<Solid>;
  };

export type CompositeSolidDefinitionSolidHandleArgs = {
  handleID: Scalars["String"]["input"];
};

export type CompositeSolidDefinitionSolidHandlesArgs = {
  parentHandleID?: InputMaybe<Scalars["String"]["input"]>;
};

export type ConcurrencyKeyInfo = {
  __typename?: "ConcurrencyKeyInfo";
  activeRunIds: Array<Scalars["String"]["output"]>;
  activeSlotCount: Scalars["Int"]["output"];
  assignedStepCount: Scalars["Int"]["output"];
  assignedStepRunIds: Array<Scalars["String"]["output"]>;
  claimedSlots: Array<ClaimedConcurrencySlot>;
  concurrencyKey: Scalars["String"]["output"];
  limit?: Maybe<Scalars["Int"]["output"]>;
  pendingStepCount: Scalars["Int"]["output"];
  pendingStepRunIds: Array<Scalars["String"]["output"]>;
  pendingSteps: Array<PendingConcurrencyStep>;
  slotCount: Scalars["Int"]["output"];
  usingDefaultLimit?: Maybe<Scalars["Boolean"]["output"]>;
};

export type ConfigType = {
  description?: Maybe<Scalars["String"]["output"]>;
  isSelector: Scalars["Boolean"]["output"];
  key: Scalars["String"]["output"];
  /**
   *
   * This is an odd and problematic field. It recursively goes down to
   * get all the types contained within a type. The case where it is horrible
   * are dictionaries and it recurses all the way down to the leaves. This means
   * that in a case where one is fetching all the types and then all the inner
   * types keys for those types, we are returning O(N^2) type keys, which
   * can cause awful performance for large schemas. When you have access
   * to *all* the types, you should instead only use the type_param_keys
   * field for closed generic types and manually navigate down the to
   * field types client-side.
   *
   * Where it is useful is when you are fetching types independently and
   * want to be able to render them, but without fetching the entire schema.
   *
   * We use this capability when rendering the sidebar.
   *
   */
  recursiveConfigTypes: Array<ConfigType>;
  /**
   *
   * This returns the keys for type parameters of any closed generic type,
   * (e.g. List, Optional). This should be used for reconstructing and
   * navigating the full schema client-side and not innerTypes.
   *
   */
  typeParamKeys: Array<Scalars["String"]["output"]>;
};

export type ConfigTypeField = {
  __typename?: "ConfigTypeField";
  configType: ConfigType;
  configTypeKey: Scalars["String"]["output"];
  defaultValueAsJson?: Maybe<Scalars["String"]["output"]>;
  description?: Maybe<Scalars["String"]["output"]>;
  isRequired: Scalars["Boolean"]["output"];
  name: Scalars["String"]["output"];
};

export type ConfigTypeNotFoundError = Error & {
  __typename?: "ConfigTypeNotFoundError";
  configTypeName: Scalars["String"]["output"];
  message: Scalars["String"]["output"];
  pipeline: Pipeline;
};

export type ConfigTypeOrError =
  | CompositeConfigType
  | ConfigTypeNotFoundError
  | EnumConfigType
  | PipelineNotFoundError
  | PythonError
  | RegularConfigType;

export type ConfiguredValue = {
  __typename?: "ConfiguredValue";
  key: Scalars["String"]["output"];
  type: ConfiguredValueType;
  value: Scalars["String"]["output"];
};

export enum ConfiguredValueType {
  EnvVar = "ENV_VAR",
  Value = "VALUE",
}

export type ConflictingExecutionParamsError = Error & {
  __typename?: "ConflictingExecutionParamsError";
  message: Scalars["String"]["output"];
};

export type DaemonHealth = {
  __typename?: "DaemonHealth";
  allDaemonStatuses: Array<DaemonStatus>;
  daemonStatus: DaemonStatus;
  id: Scalars["String"]["output"];
};

export type DaemonHealthDaemonStatusArgs = {
  daemonType?: InputMaybe<Scalars["String"]["input"]>;
};

export type DaemonStatus = {
  __typename?: "DaemonStatus";
  daemonType: Scalars["String"]["output"];
  healthy?: Maybe<Scalars["Boolean"]["output"]>;
  id: Scalars["ID"]["output"];
  lastHeartbeatErrors: Array<PythonError>;
  lastHeartbeatTime?: Maybe<Scalars["Float"]["output"]>;
  required: Scalars["Boolean"]["output"];
};

/** The types of events that may be yielded by op and job execution. */
export enum DagsterEventType {
  AlertFailure = "ALERT_FAILURE",
  AlertStart = "ALERT_START",
  AlertSuccess = "ALERT_SUCCESS",
  AssetCheckEvaluation = "ASSET_CHECK_EVALUATION",
  AssetCheckEvaluationPlanned = "ASSET_CHECK_EVALUATION_PLANNED",
  AssetMaterialization = "ASSET_MATERIALIZATION",
  AssetMaterializationPlanned = "ASSET_MATERIALIZATION_PLANNED",
  AssetObservation = "ASSET_OBSERVATION",
  AssetStoreOperation = "ASSET_STORE_OPERATION",
  EngineEvent = "ENGINE_EVENT",
  HandledOutput = "HANDLED_OUTPUT",
  HookCompleted = "HOOK_COMPLETED",
  HookErrored = "HOOK_ERRORED",
  HookSkipped = "HOOK_SKIPPED",
  LoadedInput = "LOADED_INPUT",
  LogsCaptured = "LOGS_CAPTURED",
  ObjectStoreOperation = "OBJECT_STORE_OPERATION",
  PipelineCanceled = "PIPELINE_CANCELED",
  PipelineCanceling = "PIPELINE_CANCELING",
  PipelineDequeued = "PIPELINE_DEQUEUED",
  PipelineEnqueued = "PIPELINE_ENQUEUED",
  PipelineFailure = "PIPELINE_FAILURE",
  PipelineStart = "PIPELINE_START",
  PipelineStarting = "PIPELINE_STARTING",
  PipelineSuccess = "PIPELINE_SUCCESS",
  ResourceInitFailure = "RESOURCE_INIT_FAILURE",
  ResourceInitStarted = "RESOURCE_INIT_STARTED",
  ResourceInitSuccess = "RESOURCE_INIT_SUCCESS",
  RunCanceled = "RUN_CANCELED",
  RunCanceling = "RUN_CANCELING",
  RunDequeued = "RUN_DEQUEUED",
  RunEnqueued = "RUN_ENQUEUED",
  RunFailure = "RUN_FAILURE",
  RunStart = "RUN_START",
  RunStarting = "RUN_STARTING",
  RunSuccess = "RUN_SUCCESS",
  StepExpectationResult = "STEP_EXPECTATION_RESULT",
  StepFailure = "STEP_FAILURE",
  StepInput = "STEP_INPUT",
  StepOutput = "STEP_OUTPUT",
  StepRestarted = "STEP_RESTARTED",
  StepSkipped = "STEP_SKIPPED",
  StepStart = "STEP_START",
  StepSuccess = "STEP_SUCCESS",
  StepUpForRetry = "STEP_UP_FOR_RETRY",
  StepWorkerStarted = "STEP_WORKER_STARTED",
  StepWorkerStarting = "STEP_WORKER_STARTING",
}

export type DagsterLibraryVersion = {
  __typename?: "DagsterLibraryVersion";
  name: Scalars["String"]["output"];
  version: Scalars["String"]["output"];
};

export type DagsterRunEvent =
  | AlertFailureEvent
  | AlertStartEvent
  | AlertSuccessEvent
  | AssetCheckEvaluationEvent
  | AssetCheckEvaluationPlannedEvent
  | AssetMaterializationPlannedEvent
  | EngineEvent
  | ExecutionStepFailureEvent
  | ExecutionStepInputEvent
  | ExecutionStepOutputEvent
  | ExecutionStepRestartEvent
  | ExecutionStepSkippedEvent
  | ExecutionStepStartEvent
  | ExecutionStepSuccessEvent
  | ExecutionStepUpForRetryEvent
  | HandledOutputEvent
  | HookCompletedEvent
  | HookErroredEvent
  | HookSkippedEvent
  | LoadedInputEvent
  | LogMessageEvent
  | LogsCapturedEvent
  | MaterializationEvent
  | ObjectStoreOperationEvent
  | ObservationEvent
  | ResourceInitFailureEvent
  | ResourceInitStartedEvent
  | ResourceInitSuccessEvent
  | RunCanceledEvent
  | RunCancelingEvent
  | RunDequeuedEvent
  | RunEnqueuedEvent
  | RunFailureEvent
  | RunStartEvent
  | RunStartingEvent
  | RunSuccessEvent
  | StepExpectationResultEvent
  | StepWorkerStartedEvent
  | StepWorkerStartingEvent;

export type DagsterType = {
  description?: Maybe<Scalars["String"]["output"]>;
  displayName: Scalars["String"]["output"];
  innerTypes: Array<DagsterType>;
  inputSchemaType?: Maybe<ConfigType>;
  isBuiltin: Scalars["Boolean"]["output"];
  isList: Scalars["Boolean"]["output"];
  isNothing: Scalars["Boolean"]["output"];
  isNullable: Scalars["Boolean"]["output"];
  key: Scalars["String"]["output"];
  metadataEntries: Array<MetadataEntry>;
  name?: Maybe<Scalars["String"]["output"]>;
  outputSchemaType?: Maybe<ConfigType>;
};

export type DagsterTypeNotFoundError = Error & {
  __typename?: "DagsterTypeNotFoundError";
  dagsterTypeName: Scalars["String"]["output"];
  message: Scalars["String"]["output"];
};

export type DagsterTypeOrError =
  | DagsterTypeNotFoundError
  | PipelineNotFoundError
  | PythonError
  | RegularDagsterType;

export type DefaultPartitionStatuses = {
  __typename?: "DefaultPartitionStatuses";
  failedPartitions: Array<Scalars["String"]["output"]>;
  materializedPartitions: Array<Scalars["String"]["output"]>;
  materializingPartitions: Array<Scalars["String"]["output"]>;
  unmaterializedPartitions: Array<Scalars["String"]["output"]>;
};

export type DefinitionTag = {
  __typename?: "DefinitionTag";
  key: Scalars["String"]["output"];
  value: Scalars["String"]["output"];
};

export type DeleteDynamicPartitionsResult =
  | DeleteDynamicPartitionsSuccess
  | PythonError
  | UnauthorizedError;

export type DeleteDynamicPartitionsSuccess = {
  __typename?: "DeleteDynamicPartitionsSuccess";
  partitionsDefName: Scalars["String"]["output"];
};

/** The output from deleting a run. */
export type DeletePipelineRunResult =
  | DeletePipelineRunSuccess
  | PythonError
  | RunNotFoundError
  | UnauthorizedError;

/** Output indicating that a run was deleted. */
export type DeletePipelineRunSuccess = {
  __typename?: "DeletePipelineRunSuccess";
  runId: Scalars["String"]["output"];
};

/** Deletes a run from storage. */
export type DeleteRunMutation = {
  __typename?: "DeleteRunMutation";
  Output: DeletePipelineRunResult;
};

export type DimensionDefinitionType = {
  __typename?: "DimensionDefinitionType";
  description: Scalars["String"]["output"];
  dynamicPartitionsDefinitionName?: Maybe<Scalars["String"]["output"]>;
  isPrimaryDimension: Scalars["Boolean"]["output"];
  name: Scalars["String"]["output"];
  type: PartitionDefinitionType;
};

export type DimensionPartitionKeys = {
  __typename?: "DimensionPartitionKeys";
  name: Scalars["String"]["output"];
  partitionKeys: Array<Scalars["String"]["output"]>;
  type: PartitionDefinitionType;
};

export type DisplayableEvent = {
  description?: Maybe<Scalars["String"]["output"]>;
  label?: Maybe<Scalars["String"]["output"]>;
  metadataEntries: Array<MetadataEntry>;
};

export type DryRunInstigationTick = {
  __typename?: "DryRunInstigationTick";
  evaluationResult?: Maybe<TickEvaluation>;
  timestamp?: Maybe<Scalars["Float"]["output"]>;
};

export type DryRunInstigationTicks = {
  __typename?: "DryRunInstigationTicks";
  cursor: Scalars["Float"]["output"];
  results: Array<DryRunInstigationTick>;
};

export type DuplicateDynamicPartitionError = Error & {
  __typename?: "DuplicateDynamicPartitionError";
  message: Scalars["String"]["output"];
  partitionName: Scalars["String"]["output"];
  partitionsDefName: Scalars["String"]["output"];
};

export type DynamicPartitionRequest = {
  __typename?: "DynamicPartitionRequest";
  partitionKeys?: Maybe<Array<Scalars["String"]["output"]>>;
  partitionsDefName: Scalars["String"]["output"];
  type: DynamicPartitionsRequestType;
};

export type DynamicPartitionsRequestResult = {
  __typename?: "DynamicPartitionsRequestResult";
  partitionKeys?: Maybe<Array<Scalars["String"]["output"]>>;
  partitionsDefName: Scalars["String"]["output"];
  skippedPartitionKeys: Array<Scalars["String"]["output"]>;
  type: DynamicPartitionsRequestType;
};

export enum DynamicPartitionsRequestType {
  AddPartitions = "ADD_PARTITIONS",
  DeletePartitions = "DELETE_PARTITIONS",
}

export type EngineEvent = DisplayableEvent &
  ErrorEvent &
  MarkerEvent &
  MessageEvent &
  StepEvent & {
    __typename?: "EngineEvent";
    description?: Maybe<Scalars["String"]["output"]>;
    error?: Maybe<PythonError>;
    eventType?: Maybe<DagsterEventType>;
    label?: Maybe<Scalars["String"]["output"]>;
    level: LogLevel;
    markerEnd?: Maybe<Scalars["String"]["output"]>;
    markerStart?: Maybe<Scalars["String"]["output"]>;
    message: Scalars["String"]["output"];
    metadataEntries: Array<MetadataEntry>;
    runId: Scalars["String"]["output"];
    solidHandleID?: Maybe<Scalars["String"]["output"]>;
    stepKey?: Maybe<Scalars["String"]["output"]>;
    timestamp: Scalars["String"]["output"];
  };

export type EntityKey = AssetCheckhandle | AssetKey;

export type EnumConfigType = ConfigType & {
  __typename?: "EnumConfigType";
  description?: Maybe<Scalars["String"]["output"]>;
  givenName: Scalars["String"]["output"];
  isSelector: Scalars["Boolean"]["output"];
  key: Scalars["String"]["output"];
  /**
   *
   * This is an odd and problematic field. It recursively goes down to
   * get all the types contained within a type. The case where it is horrible
   * are dictionaries and it recurses all the way down to the leaves. This means
   * that in a case where one is fetching all the types and then all the inner
   * types keys for those types, we are returning O(N^2) type keys, which
   * can cause awful performance for large schemas. When you have access
   * to *all* the types, you should instead only use the type_param_keys
   * field for closed generic types and manually navigate down the to
   * field types client-side.
   *
   * Where it is useful is when you are fetching types independently and
   * want to be able to render them, but without fetching the entire schema.
   *
   * We use this capability when rendering the sidebar.
   *
   */
  recursiveConfigTypes: Array<ConfigType>;
  /**
   *
   * This returns the keys for type parameters of any closed generic type,
   * (e.g. List, Optional). This should be used for reconstructing and
   * navigating the full schema client-side and not innerTypes.
   *
   */
  typeParamKeys: Array<Scalars["String"]["output"]>;
  values: Array<EnumConfigValue>;
};

export type EnumConfigValue = {
  __typename?: "EnumConfigValue";
  description?: Maybe<Scalars["String"]["output"]>;
  value: Scalars["String"]["output"];
};

export type EnvVarConsumer = {
  __typename?: "EnvVarConsumer";
  name: Scalars["String"]["output"];
  type: EnvVarConsumerType;
};

export enum EnvVarConsumerType {
  Resource = "RESOURCE",
}

export type EnvVarWithConsumers = {
  __typename?: "EnvVarWithConsumers";
  envVarConsumers: Array<EnvVarConsumer>;
  envVarName: Scalars["String"]["output"];
};

export type EnvVarWithConsumersList = {
  __typename?: "EnvVarWithConsumersList";
  results: Array<EnvVarWithConsumers>;
};

export type EnvVarWithConsumersOrError = EnvVarWithConsumersList | PythonError;

export type Error = {
  message: Scalars["String"]["output"];
};

export type ErrorChainLink = Error & {
  __typename?: "ErrorChainLink";
  error: PythonError;
  isExplicitLink: Scalars["Boolean"]["output"];
  message: Scalars["String"]["output"];
};

export type ErrorEvent = {
  error?: Maybe<PythonError>;
};

/** An enumeration. */
export enum ErrorSource {
  FrameworkError = "FRAMEWORK_ERROR",
  Interrupt = "INTERRUPT",
  UnexpectedError = "UNEXPECTED_ERROR",
  UserCodeError = "USER_CODE_ERROR",
}

export enum EvaluationErrorReason {
  FieldsNotDefined = "FIELDS_NOT_DEFINED",
  FieldNotDefined = "FIELD_NOT_DEFINED",
  MissingRequiredField = "MISSING_REQUIRED_FIELD",
  MissingRequiredFields = "MISSING_REQUIRED_FIELDS",
  RuntimeTypeMismatch = "RUNTIME_TYPE_MISMATCH",
  SelectorFieldError = "SELECTOR_FIELD_ERROR",
}

export type EvaluationStack = {
  __typename?: "EvaluationStack";
  entries: Array<EvaluationStackEntry>;
};

export type EvaluationStackEntry =
  | EvaluationStackListItemEntry
  | EvaluationStackMapKeyEntry
  | EvaluationStackMapValueEntry
  | EvaluationStackPathEntry;

export type EvaluationStackListItemEntry = {
  __typename?: "EvaluationStackListItemEntry";
  listIndex: Scalars["Int"]["output"];
};

export type EvaluationStackMapKeyEntry = {
  __typename?: "EvaluationStackMapKeyEntry";
  mapKey: Scalars["GenericScalar"]["output"];
};

export type EvaluationStackMapValueEntry = {
  __typename?: "EvaluationStackMapValueEntry";
  mapKey: Scalars["GenericScalar"]["output"];
};

export type EvaluationStackPathEntry = {
  __typename?: "EvaluationStackPathEntry";
  fieldName: Scalars["String"]["output"];
};

export type EventConnection = {
  __typename?: "EventConnection";
  cursor: Scalars["String"]["output"];
  events: Array<DagsterRunEvent>;
  hasMore: Scalars["Boolean"]["output"];
};

export type EventConnectionOrError =
  | EventConnection
  | PythonError
  | RunNotFoundError;

export type EventTag = {
  __typename?: "EventTag";
  key: Scalars["String"]["output"];
  value: Scalars["String"]["output"];
};

export type ExecutionMetadata = {
  /**
   * The ID of the run serving as the parent within the run group.
   *         For the first re-execution, this will be the same as the `rootRunId`. For
   *         subsequent runs, the root or a previous re-execution could be the parent run.
   */
  parentRunId?: InputMaybe<Scalars["String"]["input"]>;
  /**
   * The ID of the run at the root of the run group. All partial /
   *         full re-executions should use the first run as the rootRunID so they are
   *         grouped together.
   */
  rootRunId?: InputMaybe<Scalars["String"]["input"]>;
  tags?: InputMaybe<Array<ExecutionTag>>;
};

export type ExecutionParams = {
  /**
   * Defines run tags and parent / root relationships.
   *
   * Note: To
   *         'restart from failure', provide a `parentRunId` and pass the
   *         'dagster/is_resume_retry' tag. Dagster's automatic step key selection will
   *         override any stepKeys provided.
   */
  executionMetadata?: InputMaybe<ExecutionMetadata>;
  mode?: InputMaybe<Scalars["String"]["input"]>;
  preset?: InputMaybe<Scalars["String"]["input"]>;
  runConfigData?: InputMaybe<Scalars["RunConfigData"]["input"]>;
  /**
   * Defines the job / pipeline and solid subset that should be executed.
   *         All subsequent executions in the same run group (for example, a single-step
   *         re-execution) are scoped to the original run's selector and solid
   *         subset.
   */
  selector: JobOrPipelineSelector;
  /**
   * Defines step keys to execute within the execution plan defined
   *         by the pipeline `selector`. To execute the entire execution plan, you can omit
   *         this parameter, provide an empty array, or provide every step name.
   */
  stepKeys?: InputMaybe<Array<Scalars["String"]["input"]>>;
};

export type ExecutionPlan = {
  __typename?: "ExecutionPlan";
  artifactsPersisted: Scalars["Boolean"]["output"];
  steps: Array<ExecutionStep>;
};

export type ExecutionPlanOrError =
  | ExecutionPlan
  | InvalidSubsetError
  | PipelineNotFoundError
  | PythonError
  | RunConfigValidationInvalid;

export type ExecutionStep = {
  __typename?: "ExecutionStep";
  inputs: Array<ExecutionStepInput>;
  key: Scalars["String"]["output"];
  kind: StepKind;
  metadata: Array<MetadataItemDefinition>;
  outputs: Array<ExecutionStepOutput>;
  solidHandleID: Scalars["String"]["output"];
};

export type ExecutionStepFailureEvent = ErrorEvent &
  MessageEvent &
  StepEvent & {
    __typename?: "ExecutionStepFailureEvent";
    error?: Maybe<PythonError>;
    errorSource?: Maybe<ErrorSource>;
    eventType?: Maybe<DagsterEventType>;
    failureMetadata?: Maybe<FailureMetadata>;
    level: LogLevel;
    message: Scalars["String"]["output"];
    runId: Scalars["String"]["output"];
    solidHandleID?: Maybe<Scalars["String"]["output"]>;
    stepKey?: Maybe<Scalars["String"]["output"]>;
    timestamp: Scalars["String"]["output"];
  };

export type ExecutionStepInput = {
  __typename?: "ExecutionStepInput";
  dependsOn: Array<ExecutionStep>;
  name: Scalars["String"]["output"];
};

export type ExecutionStepInputEvent = MessageEvent &
  StepEvent & {
    __typename?: "ExecutionStepInputEvent";
    eventType?: Maybe<DagsterEventType>;
    inputName: Scalars["String"]["output"];
    level: LogLevel;
    message: Scalars["String"]["output"];
    runId: Scalars["String"]["output"];
    solidHandleID?: Maybe<Scalars["String"]["output"]>;
    stepKey?: Maybe<Scalars["String"]["output"]>;
    timestamp: Scalars["String"]["output"];
    typeCheck: TypeCheck;
  };

export type ExecutionStepOutput = {
  __typename?: "ExecutionStepOutput";
  name: Scalars["String"]["output"];
};

export type ExecutionStepOutputEvent = DisplayableEvent &
  MessageEvent &
  StepEvent & {
    __typename?: "ExecutionStepOutputEvent";
    description?: Maybe<Scalars["String"]["output"]>;
    eventType?: Maybe<DagsterEventType>;
    label?: Maybe<Scalars["String"]["output"]>;
    level: LogLevel;
    message: Scalars["String"]["output"];
    metadataEntries: Array<MetadataEntry>;
    outputName: Scalars["String"]["output"];
    runId: Scalars["String"]["output"];
    solidHandleID?: Maybe<Scalars["String"]["output"]>;
    stepKey?: Maybe<Scalars["String"]["output"]>;
    timestamp: Scalars["String"]["output"];
    typeCheck: TypeCheck;
  };

export type ExecutionStepRestartEvent = MessageEvent &
  StepEvent & {
    __typename?: "ExecutionStepRestartEvent";
    eventType?: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars["String"]["output"];
    runId: Scalars["String"]["output"];
    solidHandleID?: Maybe<Scalars["String"]["output"]>;
    stepKey?: Maybe<Scalars["String"]["output"]>;
    timestamp: Scalars["String"]["output"];
  };

export type ExecutionStepSkippedEvent = MessageEvent &
  StepEvent & {
    __typename?: "ExecutionStepSkippedEvent";
    eventType?: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars["String"]["output"];
    runId: Scalars["String"]["output"];
    solidHandleID?: Maybe<Scalars["String"]["output"]>;
    stepKey?: Maybe<Scalars["String"]["output"]>;
    timestamp: Scalars["String"]["output"];
  };

export type ExecutionStepStartEvent = MessageEvent &
  StepEvent & {
    __typename?: "ExecutionStepStartEvent";
    eventType?: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars["String"]["output"];
    runId: Scalars["String"]["output"];
    solidHandleID?: Maybe<Scalars["String"]["output"]>;
    stepKey?: Maybe<Scalars["String"]["output"]>;
    timestamp: Scalars["String"]["output"];
  };

export type ExecutionStepSuccessEvent = MessageEvent &
  StepEvent & {
    __typename?: "ExecutionStepSuccessEvent";
    eventType?: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars["String"]["output"];
    runId: Scalars["String"]["output"];
    solidHandleID?: Maybe<Scalars["String"]["output"]>;
    stepKey?: Maybe<Scalars["String"]["output"]>;
    timestamp: Scalars["String"]["output"];
  };

export type ExecutionStepUpForRetryEvent = ErrorEvent &
  MessageEvent &
  StepEvent & {
    __typename?: "ExecutionStepUpForRetryEvent";
    error?: Maybe<PythonError>;
    eventType?: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars["String"]["output"];
    runId: Scalars["String"]["output"];
    secondsToWait?: Maybe<Scalars["Int"]["output"]>;
    solidHandleID?: Maybe<Scalars["String"]["output"]>;
    stepKey?: Maybe<Scalars["String"]["output"]>;
    timestamp: Scalars["String"]["output"];
  };

export type ExecutionTag = {
  key: Scalars["String"]["input"];
  value: Scalars["String"]["input"];
};

export type ExpectationResult = DisplayableEvent & {
  __typename?: "ExpectationResult";
  description?: Maybe<Scalars["String"]["output"]>;
  label?: Maybe<Scalars["String"]["output"]>;
  metadataEntries: Array<MetadataEntry>;
  success: Scalars["Boolean"]["output"];
};

export type FailureMetadata = DisplayableEvent & {
  __typename?: "FailureMetadata";
  description?: Maybe<Scalars["String"]["output"]>;
  label?: Maybe<Scalars["String"]["output"]>;
  metadataEntries: Array<MetadataEntry>;
};

export type FeatureFlag = {
  __typename?: "FeatureFlag";
  enabled: Scalars["Boolean"]["output"];
  name: Scalars["String"]["output"];
};

export type FieldNotDefinedConfigError = PipelineConfigValidationError & {
  __typename?: "FieldNotDefinedConfigError";
  fieldName: Scalars["String"]["output"];
  message: Scalars["String"]["output"];
  path: Array<Scalars["String"]["output"]>;
  reason: EvaluationErrorReason;
  stack: EvaluationStack;
};

export type FieldsNotDefinedConfigError = PipelineConfigValidationError & {
  __typename?: "FieldsNotDefinedConfigError";
  fieldNames: Array<Scalars["String"]["output"]>;
  message: Scalars["String"]["output"];
  path: Array<Scalars["String"]["output"]>;
  reason: EvaluationErrorReason;
  stack: EvaluationStack;
};

export type FloatMetadataEntry = MetadataEntry & {
  __typename?: "FloatMetadataEntry";
  description?: Maybe<Scalars["String"]["output"]>;
  floatValue?: Maybe<Scalars["Float"]["output"]>;
  label: Scalars["String"]["output"];
};

export type FreshnessPolicy = {
  __typename?: "FreshnessPolicy";
  cronSchedule?: Maybe<Scalars["String"]["output"]>;
  cronScheduleTimezone?: Maybe<Scalars["String"]["output"]>;
  lastEvaluationTimestamp?: Maybe<Scalars["String"]["output"]>;
  maximumLagMinutes: Scalars["Float"]["output"];
};

export type Graph = SolidContainer & {
  __typename?: "Graph";
  description?: Maybe<Scalars["String"]["output"]>;
  id: Scalars["ID"]["output"];
  modes: Array<Mode>;
  name: Scalars["String"]["output"];
  solidHandle?: Maybe<SolidHandle>;
  solidHandles: Array<SolidHandle>;
  solids: Array<Solid>;
};

export type GraphSolidHandleArgs = {
  handleID: Scalars["String"]["input"];
};

export type GraphSolidHandlesArgs = {
  parentHandleID?: InputMaybe<Scalars["String"]["input"]>;
};

export type GraphNotFoundError = Error & {
  __typename?: "GraphNotFoundError";
  graphName: Scalars["String"]["output"];
  message: Scalars["String"]["output"];
  repositoryLocationName: Scalars["String"]["output"];
  repositoryName: Scalars["String"]["output"];
};

export type GraphOrError = Graph | GraphNotFoundError | PythonError;

/**
 * This type represents the fields necessary to identify a
 *         graph
 */
export type GraphSelector = {
  graphName: Scalars["String"]["input"];
  repositoryLocationName: Scalars["String"]["input"];
  repositoryName: Scalars["String"]["input"];
};

export type HandledOutputEvent = DisplayableEvent &
  MessageEvent &
  StepEvent & {
    __typename?: "HandledOutputEvent";
    description?: Maybe<Scalars["String"]["output"]>;
    eventType?: Maybe<DagsterEventType>;
    label?: Maybe<Scalars["String"]["output"]>;
    level: LogLevel;
    managerKey: Scalars["String"]["output"];
    message: Scalars["String"]["output"];
    metadataEntries: Array<MetadataEntry>;
    outputName: Scalars["String"]["output"];
    runId: Scalars["String"]["output"];
    solidHandleID?: Maybe<Scalars["String"]["output"]>;
    stepKey?: Maybe<Scalars["String"]["output"]>;
    timestamp: Scalars["String"]["output"];
  };

export type HookCompletedEvent = MessageEvent &
  StepEvent & {
    __typename?: "HookCompletedEvent";
    eventType?: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars["String"]["output"];
    runId: Scalars["String"]["output"];
    solidHandleID?: Maybe<Scalars["String"]["output"]>;
    stepKey?: Maybe<Scalars["String"]["output"]>;
    timestamp: Scalars["String"]["output"];
  };

export type HookErroredEvent = ErrorEvent &
  MessageEvent &
  StepEvent & {
    __typename?: "HookErroredEvent";
    error?: Maybe<PythonError>;
    eventType?: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars["String"]["output"];
    runId: Scalars["String"]["output"];
    solidHandleID?: Maybe<Scalars["String"]["output"]>;
    stepKey?: Maybe<Scalars["String"]["output"]>;
    timestamp: Scalars["String"]["output"];
  };

export type HookSkippedEvent = MessageEvent &
  StepEvent & {
    __typename?: "HookSkippedEvent";
    eventType?: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars["String"]["output"];
    runId: Scalars["String"]["output"];
    solidHandleID?: Maybe<Scalars["String"]["output"]>;
    stepKey?: Maybe<Scalars["String"]["output"]>;
    timestamp: Scalars["String"]["output"];
  };

export type IPipelineSnapshot = {
  dagsterTypeOrError: DagsterTypeOrError;
  dagsterTypes: Array<DagsterType>;
  description?: Maybe<Scalars["String"]["output"]>;
  graphName: Scalars["String"]["output"];
  metadataEntries: Array<MetadataEntry>;
  modes: Array<Mode>;
  name: Scalars["String"]["output"];
  parentSnapshotId?: Maybe<Scalars["String"]["output"]>;
  pipelineSnapshotId: Scalars["String"]["output"];
  runs: Array<Run>;
  schedules: Array<Schedule>;
  sensors: Array<Sensor>;
  solidHandle?: Maybe<SolidHandle>;
  solidHandles: Array<SolidHandle>;
  solids: Array<Solid>;
  tags: Array<PipelineTag>;
};

export type IPipelineSnapshotDagsterTypeOrErrorArgs = {
  dagsterTypeName: Scalars["String"]["input"];
};

export type IPipelineSnapshotRunsArgs = {
  cursor?: InputMaybe<Scalars["String"]["input"]>;
  limit?: InputMaybe<Scalars["Int"]["input"]>;
};

export type IPipelineSnapshotSolidHandleArgs = {
  handleID: Scalars["String"]["input"];
};

export type IPipelineSnapshotSolidHandlesArgs = {
  parentHandleID?: InputMaybe<Scalars["String"]["input"]>;
};

export type ISolidDefinition = {
  assetNodes: Array<AssetNode>;
  description?: Maybe<Scalars["String"]["output"]>;
  inputDefinitions: Array<InputDefinition>;
  metadata: Array<MetadataItemDefinition>;
  name: Scalars["String"]["output"];
  outputDefinitions: Array<OutputDefinition>;
  pools: Array<Scalars["String"]["output"]>;
};

export type Input = {
  __typename?: "Input";
  definition: InputDefinition;
  dependsOn: Array<Output>;
  isDynamicCollect: Scalars["Boolean"]["output"];
  solid: Solid;
};

export type InputDefinition = {
  __typename?: "InputDefinition";
  description?: Maybe<Scalars["String"]["output"]>;
  metadataEntries: Array<MetadataEntry>;
  name: Scalars["String"]["output"];
  type: DagsterType;
};

export type InputMapping = {
  __typename?: "InputMapping";
  definition: InputDefinition;
  mappedInput: Input;
};

export type Instance = {
  __typename?: "Instance";
  autoMaterializePaused: Scalars["Boolean"]["output"];
  concurrencyLimit: ConcurrencyKeyInfo;
  concurrencyLimits: Array<ConcurrencyKeyInfo>;
  daemonHealth: DaemonHealth;
  executablePath: Scalars["String"]["output"];
  hasInfo: Scalars["Boolean"]["output"];
  id: Scalars["String"]["output"];
  info?: Maybe<Scalars["String"]["output"]>;
  maxConcurrencyLimitValue: Scalars["Int"]["output"];
  minConcurrencyLimitValue: Scalars["Int"]["output"];
  poolConfig?: Maybe<PoolConfig>;
  runLauncher?: Maybe<RunLauncher>;
  runQueueConfig?: Maybe<RunQueueConfig>;
  runQueuingSupported: Scalars["Boolean"]["output"];
  supportsConcurrencyLimits: Scalars["Boolean"]["output"];
  /** Whether or not the deployment is using automation policy sensors to materialize assets */
  useAutoMaterializeSensors: Scalars["Boolean"]["output"];
};

export type InstanceConcurrencyLimitArgs = {
  concurrencyKey?: InputMaybe<Scalars["String"]["input"]>;
};

export type InstigationEvent = {
  __typename?: "InstigationEvent";
  level: LogLevel;
  message: Scalars["String"]["output"];
  timestamp: Scalars["String"]["output"];
};

export type InstigationEventConnection = {
  __typename?: "InstigationEventConnection";
  cursor: Scalars["String"]["output"];
  events: Array<InstigationEvent>;
  hasMore: Scalars["Boolean"]["output"];
};

/** This type represents the fields necessary to identify a schedule or sensor. */
export type InstigationSelector = {
  name: Scalars["String"]["input"];
  repositoryLocationName: Scalars["String"]["input"];
  repositoryName: Scalars["String"]["input"];
};

export type InstigationState = {
  __typename?: "InstigationState";
  hasStartPermission: Scalars["Boolean"]["output"];
  hasStopPermission: Scalars["Boolean"]["output"];
  id: Scalars["ID"]["output"];
  instigationType: InstigationType;
  name: Scalars["String"]["output"];
  nextTick?: Maybe<DryRunInstigationTick>;
  repositoryLocationName: Scalars["String"]["output"];
  repositoryName: Scalars["String"]["output"];
  repositoryOrigin: RepositoryOrigin;
  runningCount: Scalars["Int"]["output"];
  runs: Array<Run>;
  runsCount: Scalars["Int"]["output"];
  selectorId: Scalars["String"]["output"];
  status: InstigationStatus;
  tick: InstigationTick;
  ticks: Array<InstigationTick>;
  typeSpecificData?: Maybe<InstigationTypeSpecificData>;
};

export type InstigationStateRunsArgs = {
  limit?: InputMaybe<Scalars["Int"]["input"]>;
};

export type InstigationStateTickArgs = {
  tickId: Scalars["ID"]["input"];
};

export type InstigationStateTicksArgs = {
  afterTimestamp?: InputMaybe<Scalars["Float"]["input"]>;
  beforeTimestamp?: InputMaybe<Scalars["Float"]["input"]>;
  cursor?: InputMaybe<Scalars["String"]["input"]>;
  dayOffset?: InputMaybe<Scalars["Int"]["input"]>;
  dayRange?: InputMaybe<Scalars["Int"]["input"]>;
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  statuses?: InputMaybe<Array<InstigationTickStatus>>;
};

export type InstigationStateNotFoundError = Error & {
  __typename?: "InstigationStateNotFoundError";
  message: Scalars["String"]["output"];
  name: Scalars["String"]["output"];
};

export type InstigationStateOrError =
  | InstigationState
  | InstigationStateNotFoundError
  | PythonError;

export type InstigationStates = {
  __typename?: "InstigationStates";
  results: Array<InstigationState>;
};

export type InstigationStatesOrError = InstigationStates | PythonError;

export enum InstigationStatus {
  Running = "RUNNING",
  Stopped = "STOPPED",
}

export type InstigationTick = {
  __typename?: "InstigationTick";
  autoMaterializeAssetEvaluationId?: Maybe<Scalars["ID"]["output"]>;
  cursor?: Maybe<Scalars["String"]["output"]>;
  dynamicPartitionsRequestResults: Array<DynamicPartitionsRequestResult>;
  endTimestamp?: Maybe<Scalars["Float"]["output"]>;
  error?: Maybe<PythonError>;
  id: Scalars["ID"]["output"];
  instigationType: InstigationType;
  logEvents: InstigationEventConnection;
  logKey?: Maybe<Array<Scalars["String"]["output"]>>;
  originRunIds: Array<Scalars["String"]["output"]>;
  requestedAssetKeys: Array<AssetKey>;
  requestedAssetMaterializationCount: Scalars["Int"]["output"];
  requestedMaterializationsForAssets: Array<RequestedMaterializationsForAsset>;
  runIds: Array<Scalars["String"]["output"]>;
  runKeys: Array<Scalars["String"]["output"]>;
  runs: Array<Run>;
  skipReason?: Maybe<Scalars["String"]["output"]>;
  status: InstigationTickStatus;
  tickId: Scalars["ID"]["output"];
  timestamp: Scalars["Float"]["output"];
};

export enum InstigationTickStatus {
  Failure = "FAILURE",
  Skipped = "SKIPPED",
  Started = "STARTED",
  Success = "SUCCESS",
}

/** An enumeration. */
export enum InstigationType {
  AutoMaterialize = "AUTO_MATERIALIZE",
  Schedule = "SCHEDULE",
  Sensor = "SENSOR",
}

export type InstigationTypeSpecificData = ScheduleData | SensorData;

export type Instigator = Schedule | Sensor;

export type IntMetadataEntry = MetadataEntry & {
  __typename?: "IntMetadataEntry";
  description?: Maybe<Scalars["String"]["output"]>;
  /** String representation of the int to support greater than 32 bit */
  intRepr: Scalars["String"]["output"];
  /** Nullable to allow graceful degrade on > 32 bit numbers */
  intValue?: Maybe<Scalars["Int"]["output"]>;
  label: Scalars["String"]["output"];
};

export type InvalidOutputError = {
  __typename?: "InvalidOutputError";
  invalidOutputName: Scalars["String"]["output"];
  stepKey: Scalars["String"]["output"];
};

export type InvalidPipelineRunsFilterError = Error & {
  __typename?: "InvalidPipelineRunsFilterError";
  message: Scalars["String"]["output"];
};

export type InvalidStepError = {
  __typename?: "InvalidStepError";
  invalidStepKey: Scalars["String"]["output"];
};

export type InvalidSubsetError = Error & {
  __typename?: "InvalidSubsetError";
  message: Scalars["String"]["output"];
  pipeline: Pipeline;
};

export type Job = IPipelineSnapshot &
  SolidContainer & {
    __typename?: "Job";
    dagsterTypeOrError: DagsterTypeOrError;
    dagsterTypes: Array<DagsterType>;
    description?: Maybe<Scalars["String"]["output"]>;
    graphName: Scalars["String"]["output"];
    id: Scalars["ID"]["output"];
    isAssetJob: Scalars["Boolean"]["output"];
    isJob: Scalars["Boolean"]["output"];
    metadataEntries: Array<MetadataEntry>;
    modes: Array<Mode>;
    name: Scalars["String"]["output"];
    parentSnapshotId?: Maybe<Scalars["String"]["output"]>;
    partition?: Maybe<PartitionTagsAndConfig>;
    partitionKeysOrError: PartitionKeys;
    pipelineSnapshotId: Scalars["String"]["output"];
    presets: Array<PipelinePreset>;
    repository: Repository;
    runTags: Array<PipelineTag>;
    runs: Array<Run>;
    schedules: Array<Schedule>;
    sensors: Array<Sensor>;
    solidHandle?: Maybe<SolidHandle>;
    solidHandles: Array<SolidHandle>;
    solids: Array<Solid>;
    tags: Array<PipelineTag>;
  };

export type JobDagsterTypeOrErrorArgs = {
  dagsterTypeName: Scalars["String"]["input"];
};

export type JobPartitionArgs = {
  partitionName: Scalars["String"]["input"];
  selectedAssetKeys?: InputMaybe<Array<AssetKeyInput>>;
};

export type JobPartitionKeysOrErrorArgs = {
  cursor?: InputMaybe<Scalars["String"]["input"]>;
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  reverse?: InputMaybe<Scalars["Boolean"]["input"]>;
  selectedAssetKeys?: InputMaybe<Array<AssetKeyInput>>;
};

export type JobRunsArgs = {
  cursor?: InputMaybe<Scalars["String"]["input"]>;
  limit?: InputMaybe<Scalars["Int"]["input"]>;
};

export type JobSolidHandleArgs = {
  handleID: Scalars["String"]["input"];
};

export type JobSolidHandlesArgs = {
  parentHandleID?: InputMaybe<Scalars["String"]["input"]>;
};

export type JobMetadataEntry = MetadataEntry & {
  __typename?: "JobMetadataEntry";
  description?: Maybe<Scalars["String"]["output"]>;
  jobName: Scalars["String"]["output"];
  label: Scalars["String"]["output"];
  locationName: Scalars["String"]["output"];
  repositoryName?: Maybe<Scalars["String"]["output"]>;
};

/** This type represents the fields necessary to identify a job or pipeline */
export type JobOrPipelineSelector = {
  assetCheckSelection?: InputMaybe<Array<AssetCheckHandleInput>>;
  assetSelection?: InputMaybe<Array<AssetKeyInput>>;
  jobName?: InputMaybe<Scalars["String"]["input"]>;
  pipelineName?: InputMaybe<Scalars["String"]["input"]>;
  repositoryLocationName: Scalars["String"]["input"];
  repositoryName: Scalars["String"]["input"];
  solidSelection?: InputMaybe<Array<Scalars["String"]["input"]>>;
};

export type JobWithOps = {
  __typename?: "JobWithOps";
  jobName: Scalars["String"]["output"];
  opHandleIDs: Array<Scalars["String"]["output"]>;
};

export type JsonMetadataEntry = MetadataEntry & {
  __typename?: "JsonMetadataEntry";
  description?: Maybe<Scalars["String"]["output"]>;
  jsonString: Scalars["String"]["output"];
  label: Scalars["String"]["output"];
};

/** Launches a set of partition backfill runs. */
export type LaunchBackfillMutation = {
  __typename?: "LaunchBackfillMutation";
  Output: LaunchBackfillResult;
};

export type LaunchBackfillParams = {
  allPartitions?: InputMaybe<Scalars["Boolean"]["input"]>;
  assetSelection?: InputMaybe<Array<AssetKeyInput>>;
  description?: InputMaybe<Scalars["String"]["input"]>;
  forceSynchronousSubmission?: InputMaybe<Scalars["Boolean"]["input"]>;
  fromFailure?: InputMaybe<Scalars["Boolean"]["input"]>;
  partitionNames?: InputMaybe<Array<Scalars["String"]["input"]>>;
  partitionsByAssets?: InputMaybe<Array<InputMaybe<PartitionsByAssetSelector>>>;
  reexecutionSteps?: InputMaybe<Array<Scalars["String"]["input"]>>;
  selector?: InputMaybe<PartitionSetSelector>;
  tags?: InputMaybe<Array<ExecutionTag>>;
  title?: InputMaybe<Scalars["String"]["input"]>;
};

export type LaunchBackfillResult =
  | ConflictingExecutionParamsError
  | InvalidOutputError
  | InvalidStepError
  | InvalidSubsetError
  | LaunchBackfillSuccess
  | NoModeProvidedError
  | PartitionKeysNotFoundError
  | PartitionSetNotFoundError
  | PipelineNotFoundError
  | PresetNotFoundError
  | PythonError
  | RunConfigValidationInvalid
  | RunConflict
  | UnauthorizedError;

export type LaunchBackfillSuccess = {
  __typename?: "LaunchBackfillSuccess";
  backfillId: Scalars["String"]["output"];
  launchedRunIds?: Maybe<Array<Maybe<Scalars["String"]["output"]>>>;
};

/** Launches multiple job runs. */
export type LaunchMultipleRunsMutation = {
  __typename?: "LaunchMultipleRunsMutation";
  Output: LaunchMultipleRunsResultOrError;
};

/** Contains results from multiple pipeline launches. */
export type LaunchMultipleRunsResult = {
  __typename?: "LaunchMultipleRunsResult";
  launchMultipleRunsResult: Array<LaunchRunResult>;
};

export type LaunchMultipleRunsResultOrError =
  | LaunchMultipleRunsResult
  | PythonError;

export type LaunchPipelineRunSuccess = {
  run: Run;
};

/** Launches a job run. */
export type LaunchRunMutation = {
  __typename?: "LaunchRunMutation";
  Output: LaunchRunResult;
};

/** Re-executes a job run. */
export type LaunchRunReexecutionMutation = {
  __typename?: "LaunchRunReexecutionMutation";
  Output: LaunchRunReexecutionResult;
};

export type LaunchRunReexecutionResult =
  | ConflictingExecutionParamsError
  | InvalidOutputError
  | InvalidStepError
  | InvalidSubsetError
  | LaunchRunSuccess
  | NoModeProvidedError
  | PipelineNotFoundError
  | PresetNotFoundError
  | PythonError
  | RunConfigValidationInvalid
  | RunConflict
  | UnauthorizedError;

export type LaunchRunResult =
  | ConflictingExecutionParamsError
  | InvalidOutputError
  | InvalidStepError
  | InvalidSubsetError
  | LaunchRunSuccess
  | NoModeProvidedError
  | PipelineNotFoundError
  | PresetNotFoundError
  | PythonError
  | RunConfigValidationInvalid
  | RunConflict
  | UnauthorizedError;

export type LaunchRunSuccess = LaunchPipelineRunSuccess & {
  __typename?: "LaunchRunSuccess";
  run: Run;
};

export type ListDagsterType = DagsterType &
  WrappingDagsterType & {
    __typename?: "ListDagsterType";
    description?: Maybe<Scalars["String"]["output"]>;
    displayName: Scalars["String"]["output"];
    innerTypes: Array<DagsterType>;
    inputSchemaType?: Maybe<ConfigType>;
    isBuiltin: Scalars["Boolean"]["output"];
    isList: Scalars["Boolean"]["output"];
    isNothing: Scalars["Boolean"]["output"];
    isNullable: Scalars["Boolean"]["output"];
    key: Scalars["String"]["output"];
    metadataEntries: Array<MetadataEntry>;
    name?: Maybe<Scalars["String"]["output"]>;
    ofType: DagsterType;
    outputSchemaType?: Maybe<ConfigType>;
  };

export type LoadedInputEvent = DisplayableEvent &
  MessageEvent &
  StepEvent & {
    __typename?: "LoadedInputEvent";
    description?: Maybe<Scalars["String"]["output"]>;
    eventType?: Maybe<DagsterEventType>;
    inputName: Scalars["String"]["output"];
    label?: Maybe<Scalars["String"]["output"]>;
    level: LogLevel;
    managerKey: Scalars["String"]["output"];
    message: Scalars["String"]["output"];
    metadataEntries: Array<MetadataEntry>;
    runId: Scalars["String"]["output"];
    solidHandleID?: Maybe<Scalars["String"]["output"]>;
    stepKey?: Maybe<Scalars["String"]["output"]>;
    timestamp: Scalars["String"]["output"];
    upstreamOutputName?: Maybe<Scalars["String"]["output"]>;
    upstreamStepKey?: Maybe<Scalars["String"]["output"]>;
  };

export type LocalFileCodeReference = {
  __typename?: "LocalFileCodeReference";
  filePath: Scalars["String"]["output"];
  label?: Maybe<Scalars["String"]["output"]>;
  lineNumber?: Maybe<Scalars["Int"]["output"]>;
};

export type LocationStateChangeEvent = {
  __typename?: "LocationStateChangeEvent";
  eventType: LocationStateChangeEventType;
  locationName: Scalars["String"]["output"];
  message: Scalars["String"]["output"];
  serverId?: Maybe<Scalars["String"]["output"]>;
};

/** An enumeration. */
export enum LocationStateChangeEventType {
  LocationDisconnected = "LOCATION_DISCONNECTED",
  LocationError = "LOCATION_ERROR",
  LocationReconnected = "LOCATION_RECONNECTED",
  LocationUpdated = "LOCATION_UPDATED",
}

export type LocationStateChangeSubscription = {
  __typename?: "LocationStateChangeSubscription";
  event: LocationStateChangeEvent;
};

export enum LogLevel {
  Critical = "CRITICAL",
  Debug = "DEBUG",
  Error = "ERROR",
  Info = "INFO",
  Warning = "WARNING",
}

export type LogMessageEvent = MessageEvent & {
  __typename?: "LogMessageEvent";
  eventType?: Maybe<DagsterEventType>;
  level: LogLevel;
  message: Scalars["String"]["output"];
  runId: Scalars["String"]["output"];
  solidHandleID?: Maybe<Scalars["String"]["output"]>;
  stepKey?: Maybe<Scalars["String"]["output"]>;
  timestamp: Scalars["String"]["output"];
};

export type LogRetrievalShellCommand = {
  __typename?: "LogRetrievalShellCommand";
  stderr?: Maybe<Scalars["String"]["output"]>;
  stdout?: Maybe<Scalars["String"]["output"]>;
};

/** The output from logging telemetry. */
export type LogTelemetryMutationResult = LogTelemetrySuccess | PythonError;

/** Output indicating that telemetry was logged. */
export type LogTelemetrySuccess = {
  __typename?: "LogTelemetrySuccess";
  action: Scalars["String"]["output"];
};

export type Logger = {
  __typename?: "Logger";
  configField?: Maybe<ConfigTypeField>;
  description?: Maybe<Scalars["String"]["output"]>;
  name: Scalars["String"]["output"];
};

export type LogsCapturedEvent = MessageEvent & {
  __typename?: "LogsCapturedEvent";
  eventType?: Maybe<DagsterEventType>;
  externalStderrUrl?: Maybe<Scalars["String"]["output"]>;
  externalStdoutUrl?: Maybe<Scalars["String"]["output"]>;
  externalUrl?: Maybe<Scalars["String"]["output"]>;
  fileKey: Scalars["String"]["output"];
  level: LogLevel;
  logKey: Scalars["String"]["output"];
  message: Scalars["String"]["output"];
  pid?: Maybe<Scalars["Int"]["output"]>;
  runId: Scalars["String"]["output"];
  shellCmd?: Maybe<LogRetrievalShellCommand>;
  solidHandleID?: Maybe<Scalars["String"]["output"]>;
  stepKey?: Maybe<Scalars["String"]["output"]>;
  stepKeys?: Maybe<Array<Scalars["String"]["output"]>>;
  timestamp: Scalars["String"]["output"];
};

export type MapConfigType = ConfigType & {
  __typename?: "MapConfigType";
  description?: Maybe<Scalars["String"]["output"]>;
  isSelector: Scalars["Boolean"]["output"];
  key: Scalars["String"]["output"];
  keyLabelName?: Maybe<Scalars["String"]["output"]>;
  keyType: ConfigType;
  /**
   *
   * This is an odd and problematic field. It recursively goes down to
   * get all the types contained within a type. The case where it is horrible
   * are dictionaries and it recurses all the way down to the leaves. This means
   * that in a case where one is fetching all the types and then all the inner
   * types keys for those types, we are returning O(N^2) type keys, which
   * can cause awful performance for large schemas. When you have access
   * to *all* the types, you should instead only use the type_param_keys
   * field for closed generic types and manually navigate down the to
   * field types client-side.
   *
   * Where it is useful is when you are fetching types independently and
   * want to be able to render them, but without fetching the entire schema.
   *
   * We use this capability when rendering the sidebar.
   *
   */
  recursiveConfigTypes: Array<ConfigType>;
  /**
   *
   * This returns the keys for type parameters of any closed generic type,
   * (e.g. List, Optional). This should be used for reconstructing and
   * navigating the full schema client-side and not innerTypes.
   *
   */
  typeParamKeys: Array<Scalars["String"]["output"]>;
  valueType: ConfigType;
};

export type MarkdownMetadataEntry = MetadataEntry & {
  __typename?: "MarkdownMetadataEntry";
  description?: Maybe<Scalars["String"]["output"]>;
  label: Scalars["String"]["output"];
  mdStr: Scalars["String"]["output"];
};

export type MarkerEvent = {
  markerEnd?: Maybe<Scalars["String"]["output"]>;
  markerStart?: Maybe<Scalars["String"]["output"]>;
};

export type MarshalledInput = {
  inputName: Scalars["String"]["input"];
  key: Scalars["String"]["input"];
};

export type MarshalledOutput = {
  key: Scalars["String"]["input"];
  outputName: Scalars["String"]["input"];
};

export type MaterializationEvent = DisplayableEvent &
  MessageEvent &
  StepEvent & {
    __typename?: "MaterializationEvent";
    assetKey?: Maybe<AssetKey>;
    assetLineage: Array<AssetLineageInfo>;
    description?: Maybe<Scalars["String"]["output"]>;
    eventType?: Maybe<DagsterEventType>;
    label?: Maybe<Scalars["String"]["output"]>;
    level: LogLevel;
    message: Scalars["String"]["output"];
    metadataEntries: Array<MetadataEntry>;
    partition?: Maybe<Scalars["String"]["output"]>;
    runId: Scalars["String"]["output"];
    runOrError: RunOrError;
    solidHandleID?: Maybe<Scalars["String"]["output"]>;
    stepKey?: Maybe<Scalars["String"]["output"]>;
    stepStats: RunStepStats;
    tags: Array<EventTag>;
    timestamp: Scalars["String"]["output"];
  };

export type MaterializationUpstreamDataVersion = {
  __typename?: "MaterializationUpstreamDataVersion";
  assetKey: AssetKey;
  downstreamAssetKey: AssetKey;
  timestamp: Scalars["String"]["output"];
};

/**
 * The primary dimension of a multipartitioned asset is the time-partitioned dimension.
 * If both dimensions of the asset are static or time-partitioned, the primary dimension is
 * the first defined dimension.
 */
export type MaterializedPartitionRangeStatuses2D = {
  __typename?: "MaterializedPartitionRangeStatuses2D";
  primaryDimEndKey: Scalars["String"]["output"];
  primaryDimEndTime?: Maybe<Scalars["Float"]["output"]>;
  primaryDimStartKey: Scalars["String"]["output"];
  primaryDimStartTime?: Maybe<Scalars["Float"]["output"]>;
  secondaryDim: PartitionStatus1D;
};

export type MessageEvent = {
  eventType?: Maybe<DagsterEventType>;
  level: LogLevel;
  message: Scalars["String"]["output"];
  runId: Scalars["String"]["output"];
  solidHandleID?: Maybe<Scalars["String"]["output"]>;
  stepKey?: Maybe<Scalars["String"]["output"]>;
  timestamp: Scalars["String"]["output"];
};

export type MetadataEntry = {
  description?: Maybe<Scalars["String"]["output"]>;
  label: Scalars["String"]["output"];
};

export type MetadataItemDefinition = {
  __typename?: "MetadataItemDefinition";
  key: Scalars["String"]["output"];
  value: Scalars["String"]["output"];
};

export type MissingFieldConfigError = PipelineConfigValidationError & {
  __typename?: "MissingFieldConfigError";
  field: ConfigTypeField;
  message: Scalars["String"]["output"];
  path: Array<Scalars["String"]["output"]>;
  reason: EvaluationErrorReason;
  stack: EvaluationStack;
};

export type MissingFieldsConfigError = PipelineConfigValidationError & {
  __typename?: "MissingFieldsConfigError";
  fields: Array<ConfigTypeField>;
  message: Scalars["String"]["output"];
  path: Array<Scalars["String"]["output"]>;
  reason: EvaluationErrorReason;
  stack: EvaluationStack;
};

export type MissingRunIdErrorEvent = {
  __typename?: "MissingRunIdErrorEvent";
  invalidRunId: Scalars["String"]["output"];
};

export type Mode = {
  __typename?: "Mode";
  description?: Maybe<Scalars["String"]["output"]>;
  id: Scalars["String"]["output"];
  loggers: Array<Logger>;
  name: Scalars["String"]["output"];
  resources: Array<Resource>;
};

export type ModeNotFoundError = Error & {
  __typename?: "ModeNotFoundError";
  message: Scalars["String"]["output"];
  mode: Scalars["String"]["output"];
};

export type MultiPartitionStatuses = {
  __typename?: "MultiPartitionStatuses";
  primaryDimensionName: Scalars["String"]["output"];
  ranges: Array<MaterializedPartitionRangeStatuses2D>;
};

/** The root for all mutations to modify data in your Dagster instance. */
export type Mutation = {
  __typename?: "Mutation";
  _no_fields_accessible?: Maybe<Scalars["String"]["output"]>;
  /** Adds a partition to a dynamic partition set. */
  addDynamicPartition: AddDynamicPartitionResult;
  /** Cancels a set of partition backfill runs. */
  cancelPartitionBackfill: CancelBackfillResult;
  /** Sets the concurrency limit for a given concurrency key. */
  deleteConcurrencyLimit: Scalars["Boolean"]["output"];
  /** Deletes partitions from a dynamic partition set. */
  deleteDynamicPartitions: DeleteDynamicPartitionsResult;
  /** Deletes a run from storage. */
  deletePipelineRun: DeletePipelineRunResult;
  /** Deletes a run from storage. */
  deleteRun: DeletePipelineRunResult;
  /** Frees concurrency slots. */
  freeConcurrencySlots: Scalars["Boolean"]["output"];
  /** Frees the concurrency slots occupied by a specific run. */
  freeConcurrencySlotsForRun: Scalars["Boolean"]["output"];
  /** Launches multiple job runs. */
  launchMultipleRuns: LaunchMultipleRunsResultOrError;
  /** Launches a set of partition backfill runs. */
  launchPartitionBackfill: LaunchBackfillResult;
  /** Launches a job run. */
  launchPipelineExecution: LaunchRunResult;
  /** Re-executes a job run. */
  launchPipelineReexecution: LaunchRunReexecutionResult;
  /** Launches a job run. */
  launchRun: LaunchRunResult;
  /** Re-executes a job run. */
  launchRunReexecution: LaunchRunReexecutionResult;
  /** Log telemetry about the Dagster instance. */
  logTelemetry: LogTelemetryMutationResult;
  /** Retries a set of partition backfill runs. Retrying a backfill will create a new backfill to retry any failed partitions. */
  reexecutePartitionBackfill: LaunchBackfillResult;
  /** Reloads a code location server. */
  reloadRepositoryLocation: ReloadRepositoryLocationMutationResult;
  /** Reloads the workspace and its code location servers. */
  reloadWorkspace: ReloadWorkspaceMutationResult;
  /** Reports runless events for an asset or a subset of its partitions. */
  reportRunlessAssetEvents: ReportRunlessAssetEventsResult;
  /** Reset a schedule to its status defined in code, otherwise disable it from launching runs for a job. */
  resetSchedule: ScheduleMutationResult;
  /** Reset a sensor to its status defined in code, otherwise disable it from launching runs for a job. */
  resetSensor: SensorOrError;
  /** Resumes a set of partition backfill runs. Resuming a backfill will not retry any failed runs. */
  resumePartitionBackfill: ResumeBackfillResult;
  /** Enable a schedule to launch runs for a job based on external state change. */
  scheduleDryRun: ScheduleDryRunResult;
  /** Enable a sensor to launch runs for a job based on external state change. */
  sensorDryRun: SensorDryRunResult;
  /** Toggle asset auto materializing on or off. */
  setAutoMaterializePaused: Scalars["Boolean"]["output"];
  /** Sets the concurrency limit for a given concurrency key. */
  setConcurrencyLimit: Scalars["Boolean"]["output"];
  /** Store whether we've shown the nux to any user and they've dismissed or submitted it. */
  setNuxSeen: Scalars["Boolean"]["output"];
  /** Set a cursor for a sensor to track state across evaluations. */
  setSensorCursor: SensorOrError;
  /** Shuts down a code location server. */
  shutdownRepositoryLocation: ShutdownRepositoryLocationMutationResult;
  /** Enable a schedule to launch runs for a job at a fixed interval. */
  startSchedule: ScheduleMutationResult;
  /** Enable a sensor to launch runs for a job based on external state change. */
  startSensor: SensorOrError;
  /** Disable a schedule from launching runs for a job. */
  stopRunningSchedule: ScheduleMutationResult;
  /** Disable a sensor from launching runs for a job. */
  stopSensor: StopSensorMutationResultOrError;
  /** Terminates a run. */
  terminatePipelineExecution: TerminateRunResult;
  /** Terminates a run. */
  terminateRun: TerminateRunResult;
  /** Terminates a set of runs given their run IDs. */
  terminateRuns: TerminateRunsResultOrError;
  /** Deletes asset history from storage. */
  wipeAssets: AssetWipeMutationResult;
};

/** The root for all mutations to modify data in your Dagster instance. */
export type MutationAddDynamicPartitionArgs = {
  partitionKey: Scalars["String"]["input"];
  partitionsDefName: Scalars["String"]["input"];
  repositorySelector: RepositorySelector;
};

/** The root for all mutations to modify data in your Dagster instance. */
export type MutationCancelPartitionBackfillArgs = {
  backfillId: Scalars["String"]["input"];
};

/** The root for all mutations to modify data in your Dagster instance. */
export type MutationDeleteConcurrencyLimitArgs = {
  concurrencyKey: Scalars["String"]["input"];
};

/** The root for all mutations to modify data in your Dagster instance. */
export type MutationDeleteDynamicPartitionsArgs = {
  partitionKeys: Array<Scalars["String"]["input"]>;
  partitionsDefName: Scalars["String"]["input"];
  repositorySelector: RepositorySelector;
};

/** The root for all mutations to modify data in your Dagster instance. */
export type MutationDeletePipelineRunArgs = {
  runId: Scalars["String"]["input"];
};

/** The root for all mutations to modify data in your Dagster instance. */
export type MutationDeleteRunArgs = {
  runId: Scalars["String"]["input"];
};

/** The root for all mutations to modify data in your Dagster instance. */
export type MutationFreeConcurrencySlotsArgs = {
  runId: Scalars["String"]["input"];
  stepKey?: InputMaybe<Scalars["String"]["input"]>;
};

/** The root for all mutations to modify data in your Dagster instance. */
export type MutationFreeConcurrencySlotsForRunArgs = {
  runId: Scalars["String"]["input"];
};

/** The root for all mutations to modify data in your Dagster instance. */
export type MutationLaunchMultipleRunsArgs = {
  executionParamsList: Array<ExecutionParams>;
};

/** The root for all mutations to modify data in your Dagster instance. */
export type MutationLaunchPartitionBackfillArgs = {
  backfillParams: LaunchBackfillParams;
};

/** The root for all mutations to modify data in your Dagster instance. */
export type MutationLaunchPipelineExecutionArgs = {
  executionParams: ExecutionParams;
};

/** The root for all mutations to modify data in your Dagster instance. */
export type MutationLaunchPipelineReexecutionArgs = {
  executionParams?: InputMaybe<ExecutionParams>;
  reexecutionParams?: InputMaybe<ReexecutionParams>;
};

/** The root for all mutations to modify data in your Dagster instance. */
export type MutationLaunchRunArgs = {
  executionParams: ExecutionParams;
};

/** The root for all mutations to modify data in your Dagster instance. */
export type MutationLaunchRunReexecutionArgs = {
  executionParams?: InputMaybe<ExecutionParams>;
  reexecutionParams?: InputMaybe<ReexecutionParams>;
};

/** The root for all mutations to modify data in your Dagster instance. */
export type MutationLogTelemetryArgs = {
  action: Scalars["String"]["input"];
  clientId: Scalars["String"]["input"];
  clientTime: Scalars["String"]["input"];
  metadata: Scalars["String"]["input"];
};

/** The root for all mutations to modify data in your Dagster instance. */
export type MutationReexecutePartitionBackfillArgs = {
  reexecutionParams?: InputMaybe<ReexecutionParams>;
};

/** The root for all mutations to modify data in your Dagster instance. */
export type MutationReloadRepositoryLocationArgs = {
  repositoryLocationName: Scalars["String"]["input"];
};

/** The root for all mutations to modify data in your Dagster instance. */
export type MutationReportRunlessAssetEventsArgs = {
  eventParams: ReportRunlessAssetEventsParams;
};

/** The root for all mutations to modify data in your Dagster instance. */
export type MutationResetScheduleArgs = {
  scheduleSelector: ScheduleSelector;
};

/** The root for all mutations to modify data in your Dagster instance. */
export type MutationResetSensorArgs = {
  sensorSelector: SensorSelector;
};

/** The root for all mutations to modify data in your Dagster instance. */
export type MutationResumePartitionBackfillArgs = {
  backfillId: Scalars["String"]["input"];
};

/** The root for all mutations to modify data in your Dagster instance. */
export type MutationScheduleDryRunArgs = {
  selectorData: ScheduleSelector;
  timestamp?: InputMaybe<Scalars["Float"]["input"]>;
};

/** The root for all mutations to modify data in your Dagster instance. */
export type MutationSensorDryRunArgs = {
  cursor?: InputMaybe<Scalars["String"]["input"]>;
  selectorData: SensorSelector;
};

/** The root for all mutations to modify data in your Dagster instance. */
export type MutationSetAutoMaterializePausedArgs = {
  paused: Scalars["Boolean"]["input"];
};

/** The root for all mutations to modify data in your Dagster instance. */
export type MutationSetConcurrencyLimitArgs = {
  concurrencyKey: Scalars["String"]["input"];
  limit: Scalars["Int"]["input"];
};

/** The root for all mutations to modify data in your Dagster instance. */
export type MutationSetSensorCursorArgs = {
  cursor?: InputMaybe<Scalars["String"]["input"]>;
  sensorSelector: SensorSelector;
};

/** The root for all mutations to modify data in your Dagster instance. */
export type MutationShutdownRepositoryLocationArgs = {
  repositoryLocationName: Scalars["String"]["input"];
};

/** The root for all mutations to modify data in your Dagster instance. */
export type MutationStartScheduleArgs = {
  scheduleSelector: ScheduleSelector;
};

/** The root for all mutations to modify data in your Dagster instance. */
export type MutationStartSensorArgs = {
  sensorSelector: SensorSelector;
};

/** The root for all mutations to modify data in your Dagster instance. */
export type MutationStopRunningScheduleArgs = {
  id?: InputMaybe<Scalars["String"]["input"]>;
  scheduleOriginId?: InputMaybe<Scalars["String"]["input"]>;
  scheduleSelectorId?: InputMaybe<Scalars["String"]["input"]>;
};

/** The root for all mutations to modify data in your Dagster instance. */
export type MutationStopSensorArgs = {
  id?: InputMaybe<Scalars["String"]["input"]>;
  jobOriginId?: InputMaybe<Scalars["String"]["input"]>;
  jobSelectorId?: InputMaybe<Scalars["String"]["input"]>;
};

/** The root for all mutations to modify data in your Dagster instance. */
export type MutationTerminatePipelineExecutionArgs = {
  runId: Scalars["String"]["input"];
  terminatePolicy?: InputMaybe<TerminateRunPolicy>;
};

/** The root for all mutations to modify data in your Dagster instance. */
export type MutationTerminateRunArgs = {
  runId: Scalars["String"]["input"];
  terminatePolicy?: InputMaybe<TerminateRunPolicy>;
};

/** The root for all mutations to modify data in your Dagster instance. */
export type MutationTerminateRunsArgs = {
  runIds: Array<Scalars["String"]["input"]>;
  terminatePolicy?: InputMaybe<TerminateRunPolicy>;
};

/** The root for all mutations to modify data in your Dagster instance. */
export type MutationWipeAssetsArgs = {
  assetPartitionRanges: Array<PartitionsByAssetSelector>;
};

export type NestedResourceEntry = {
  __typename?: "NestedResourceEntry";
  name: Scalars["String"]["output"];
  resource?: Maybe<ResourceDetails>;
  type: NestedResourceType;
};

/** An enumeration. */
export enum NestedResourceType {
  Anonymous = "ANONYMOUS",
  TopLevel = "TOP_LEVEL",
}

export type NoModeProvidedError = Error & {
  __typename?: "NoModeProvidedError";
  message: Scalars["String"]["output"];
  pipelineName: Scalars["String"]["output"];
};

/** An invocation of a solid within a repo. */
export type NodeInvocationSite = {
  __typename?: "NodeInvocationSite";
  pipeline: Pipeline;
  solidHandle: SolidHandle;
};

export type NotebookMetadataEntry = MetadataEntry & {
  __typename?: "NotebookMetadataEntry";
  description?: Maybe<Scalars["String"]["output"]>;
  label: Scalars["String"]["output"];
  path: Scalars["String"]["output"];
};

export type NullMetadataEntry = MetadataEntry & {
  __typename?: "NullMetadataEntry";
  description?: Maybe<Scalars["String"]["output"]>;
  label: Scalars["String"]["output"];
};

export type NullableConfigType = ConfigType &
  WrappingConfigType & {
    __typename?: "NullableConfigType";
    description?: Maybe<Scalars["String"]["output"]>;
    isSelector: Scalars["Boolean"]["output"];
    key: Scalars["String"]["output"];
    ofType: ConfigType;
    /**
     *
     * This is an odd and problematic field. It recursively goes down to
     * get all the types contained within a type. The case where it is horrible
     * are dictionaries and it recurses all the way down to the leaves. This means
     * that in a case where one is fetching all the types and then all the inner
     * types keys for those types, we are returning O(N^2) type keys, which
     * can cause awful performance for large schemas. When you have access
     * to *all* the types, you should instead only use the type_param_keys
     * field for closed generic types and manually navigate down the to
     * field types client-side.
     *
     * Where it is useful is when you are fetching types independently and
     * want to be able to render them, but without fetching the entire schema.
     *
     * We use this capability when rendering the sidebar.
     *
     */
    recursiveConfigTypes: Array<ConfigType>;
    /**
     *
     * This returns the keys for type parameters of any closed generic type,
     * (e.g. List, Optional). This should be used for reconstructing and
     * navigating the full schema client-side and not innerTypes.
     *
     */
    typeParamKeys: Array<Scalars["String"]["output"]>;
  };

export type NullableDagsterType = DagsterType &
  WrappingDagsterType & {
    __typename?: "NullableDagsterType";
    description?: Maybe<Scalars["String"]["output"]>;
    displayName: Scalars["String"]["output"];
    innerTypes: Array<DagsterType>;
    inputSchemaType?: Maybe<ConfigType>;
    isBuiltin: Scalars["Boolean"]["output"];
    isList: Scalars["Boolean"]["output"];
    isNothing: Scalars["Boolean"]["output"];
    isNullable: Scalars["Boolean"]["output"];
    key: Scalars["String"]["output"];
    metadataEntries: Array<MetadataEntry>;
    name?: Maybe<Scalars["String"]["output"]>;
    ofType: DagsterType;
    outputSchemaType?: Maybe<ConfigType>;
  };

export type ObjectStoreOperationEvent = MessageEvent &
  StepEvent & {
    __typename?: "ObjectStoreOperationEvent";
    eventType?: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars["String"]["output"];
    operationResult: ObjectStoreOperationResult;
    runId: Scalars["String"]["output"];
    solidHandleID?: Maybe<Scalars["String"]["output"]>;
    stepKey?: Maybe<Scalars["String"]["output"]>;
    timestamp: Scalars["String"]["output"];
  };

export type ObjectStoreOperationResult = DisplayableEvent & {
  __typename?: "ObjectStoreOperationResult";
  description?: Maybe<Scalars["String"]["output"]>;
  label?: Maybe<Scalars["String"]["output"]>;
  metadataEntries: Array<MetadataEntry>;
  op: ObjectStoreOperationType;
};

export enum ObjectStoreOperationType {
  CpObject = "CP_OBJECT",
  GetObject = "GET_OBJECT",
  RmObject = "RM_OBJECT",
  SetObject = "SET_OBJECT",
}

export type ObservationEvent = DisplayableEvent &
  MessageEvent &
  StepEvent & {
    __typename?: "ObservationEvent";
    assetKey?: Maybe<AssetKey>;
    description?: Maybe<Scalars["String"]["output"]>;
    eventType?: Maybe<DagsterEventType>;
    label?: Maybe<Scalars["String"]["output"]>;
    level: LogLevel;
    message: Scalars["String"]["output"];
    metadataEntries: Array<MetadataEntry>;
    partition?: Maybe<Scalars["String"]["output"]>;
    runId: Scalars["String"]["output"];
    runOrError: RunOrError;
    solidHandleID?: Maybe<Scalars["String"]["output"]>;
    stepKey?: Maybe<Scalars["String"]["output"]>;
    stepStats: RunStepStats;
    tags: Array<EventTag>;
    timestamp: Scalars["String"]["output"];
  };

export enum OrderBy {
  /** Sorts the data in ascending order */
  Asc = "Asc",
  /** Sorts the data in descending order */
  Desc = "Desc",
}

export type Oso_ArtifactsByCollectionV1 = {
  __typename?: "Oso_ArtifactsByCollectionV1";
  artifactId: Scalars["String"]["output"];
  artifactName: Scalars["String"]["output"];
  artifactNamespace: Scalars["String"]["output"];
  artifactSource: Scalars["String"]["output"];
  artifactSourceId: Scalars["String"]["output"];
  collectionId: Scalars["String"]["output"];
  collectionName: Scalars["String"]["output"];
  collectionNamespace: Scalars["String"]["output"];
  collectionSource: Scalars["String"]["output"];
};

export type Oso_ArtifactsByCollectionV1BoolExp = {
  _and?: InputMaybe<Array<Oso_ArtifactsByCollectionV1BoolExp>>;
  _not?: InputMaybe<Oso_ArtifactsByCollectionV1BoolExp>;
  _or?: InputMaybe<Array<Oso_ArtifactsByCollectionV1BoolExp>>;
  artifactId?: InputMaybe<Oso_StringBoolExp>;
  artifactName?: InputMaybe<Oso_StringBoolExp>;
  artifactNamespace?: InputMaybe<Oso_StringBoolExp>;
  artifactSource?: InputMaybe<Oso_StringBoolExp>;
  artifactSourceId?: InputMaybe<Oso_StringBoolExp>;
  collectionId?: InputMaybe<Oso_StringBoolExp>;
  collectionName?: InputMaybe<Oso_StringBoolExp>;
  collectionNamespace?: InputMaybe<Oso_StringBoolExp>;
  collectionSource?: InputMaybe<Oso_StringBoolExp>;
};

export type Oso_ArtifactsByCollectionV1OrderByExp = {
  artifactId?: InputMaybe<OrderBy>;
  artifactName?: InputMaybe<OrderBy>;
  artifactNamespace?: InputMaybe<OrderBy>;
  artifactSource?: InputMaybe<OrderBy>;
  artifactSourceId?: InputMaybe<OrderBy>;
  collectionId?: InputMaybe<OrderBy>;
  collectionName?: InputMaybe<OrderBy>;
  collectionNamespace?: InputMaybe<OrderBy>;
  collectionSource?: InputMaybe<OrderBy>;
};

export type Oso_ArtifactsByProjectV1 = {
  __typename?: "Oso_ArtifactsByProjectV1";
  artifactId: Scalars["String"]["output"];
  artifactName: Scalars["String"]["output"];
  artifactNamespace: Scalars["String"]["output"];
  artifactSource: Scalars["String"]["output"];
  artifactSourceId: Scalars["String"]["output"];
  projectId: Scalars["String"]["output"];
  projectName: Scalars["String"]["output"];
  projectNamespace: Scalars["String"]["output"];
  projectSource: Scalars["String"]["output"];
};

export type Oso_ArtifactsByProjectV1BoolExp = {
  _and?: InputMaybe<Array<Oso_ArtifactsByProjectV1BoolExp>>;
  _not?: InputMaybe<Oso_ArtifactsByProjectV1BoolExp>;
  _or?: InputMaybe<Array<Oso_ArtifactsByProjectV1BoolExp>>;
  artifactId?: InputMaybe<Oso_StringBoolExp>;
  artifactName?: InputMaybe<Oso_StringBoolExp>;
  artifactNamespace?: InputMaybe<Oso_StringBoolExp>;
  artifactSource?: InputMaybe<Oso_StringBoolExp>;
  artifactSourceId?: InputMaybe<Oso_StringBoolExp>;
  projectId?: InputMaybe<Oso_StringBoolExp>;
  projectName?: InputMaybe<Oso_StringBoolExp>;
  projectNamespace?: InputMaybe<Oso_StringBoolExp>;
  projectSource?: InputMaybe<Oso_StringBoolExp>;
};

export type Oso_ArtifactsByProjectV1OrderBy = {
  artifactId?: InputMaybe<OrderBy>;
  artifactName?: InputMaybe<OrderBy>;
  artifactNamespace?: InputMaybe<OrderBy>;
  artifactSource?: InputMaybe<OrderBy>;
  artifactSourceId?: InputMaybe<OrderBy>;
  projectId?: InputMaybe<OrderBy>;
  projectName?: InputMaybe<OrderBy>;
  projectNamespace?: InputMaybe<OrderBy>;
  projectSource?: InputMaybe<OrderBy>;
};

export type Oso_ArtifactsByUserV1 = {
  __typename?: "Oso_ArtifactsByUserV1";
  artifactId: Scalars["String"]["output"];
  artifactName: Scalars["String"]["output"];
  artifactNamespace: Scalars["String"]["output"];
  artifactSource: Scalars["String"]["output"];
  artifactSourceId: Scalars["String"]["output"];
  userId: Scalars["String"]["output"];
  userName: Scalars["String"]["output"];
  userNamespace: Scalars["String"]["output"];
  userSource: Scalars["String"]["output"];
  userSourceId: Scalars["String"]["output"];
  userType: Scalars["String"]["output"];
};

export type Oso_ArtifactsByUserV1BoolExp = {
  _and?: InputMaybe<Array<Oso_ArtifactsByUserV1BoolExp>>;
  _not?: InputMaybe<Oso_ArtifactsByUserV1BoolExp>;
  _or?: InputMaybe<Array<Oso_ArtifactsByUserV1BoolExp>>;
  artifactId?: InputMaybe<Oso_StringBoolExp>;
  artifactName?: InputMaybe<Oso_StringBoolExp>;
  artifactNamespace?: InputMaybe<Oso_StringBoolExp>;
  artifactSource?: InputMaybe<Oso_StringBoolExp>;
  artifactSourceId?: InputMaybe<Oso_StringBoolExp>;
  userId?: InputMaybe<Oso_StringBoolExp>;
  userName?: InputMaybe<Oso_StringBoolExp>;
  userNamespace?: InputMaybe<Oso_StringBoolExp>;
  userSource?: InputMaybe<Oso_StringBoolExp>;
  userSourceId?: InputMaybe<Oso_StringBoolExp>;
  userType?: InputMaybe<Oso_StringBoolExp>;
};

export type Oso_ArtifactsByUserV1OrderByExp = {
  artifactId?: InputMaybe<OrderBy>;
  artifactName?: InputMaybe<OrderBy>;
  artifactNamespace?: InputMaybe<OrderBy>;
  artifactSource?: InputMaybe<OrderBy>;
  artifactSourceId?: InputMaybe<OrderBy>;
  userId?: InputMaybe<OrderBy>;
  userName?: InputMaybe<OrderBy>;
  userNamespace?: InputMaybe<OrderBy>;
  userSource?: InputMaybe<OrderBy>;
  userSourceId?: InputMaybe<OrderBy>;
  userType?: InputMaybe<OrderBy>;
};

export type Oso_ArtifactsV1 = {
  __typename?: "Oso_ArtifactsV1";
  artifactId: Scalars["String"]["output"];
  artifactName: Scalars["String"]["output"];
  artifactNamespace: Scalars["String"]["output"];
  artifactSource: Scalars["String"]["output"];
  artifactSourceId: Scalars["String"]["output"];
};

export type Oso_ArtifactsV1BoolExp = {
  _and?: InputMaybe<Array<Oso_ArtifactsV1BoolExp>>;
  _not?: InputMaybe<Oso_ArtifactsV1BoolExp>;
  _or?: InputMaybe<Array<Oso_ArtifactsV1BoolExp>>;
  artifactId?: InputMaybe<Oso_StringBoolExp>;
  artifactName?: InputMaybe<Oso_StringBoolExp>;
  artifactNamespace?: InputMaybe<Oso_StringBoolExp>;
  artifactSource?: InputMaybe<Oso_StringBoolExp>;
  artifactSourceId?: InputMaybe<Oso_StringBoolExp>;
};

export type Oso_ArtifactsV1OrderByExp = {
  artifactId?: InputMaybe<OrderBy>;
  artifactName?: InputMaybe<OrderBy>;
  artifactNamespace?: InputMaybe<OrderBy>;
  artifactSource?: InputMaybe<OrderBy>;
  artifactSourceId?: InputMaybe<OrderBy>;
};

export type Oso_BoolBoolExp = {
  _eq?: InputMaybe<Scalars["Oso_Bool"]["input"]>;
  _in?: InputMaybe<Array<Scalars["Oso_Bool"]["input"]>>;
  _is_null?: InputMaybe<Scalars["Boolean"]["input"]>;
  _neq?: InputMaybe<Scalars["Oso_Bool"]["input"]>;
  _nin?: InputMaybe<Array<Scalars["Oso_Bool"]["input"]>>;
};

export type Oso_CodeMetricsByArtifactV0 = {
  __typename?: "Oso_CodeMetricsByArtifactV0";
  activeDeveloperCount6Months: Scalars["Oso_Float32"]["output"];
  artifactId: Scalars["String"]["output"];
  artifactName: Scalars["String"]["output"];
  artifactNamespace: Scalars["String"]["output"];
  closedIssueCount6Months: Scalars["Oso_Float32"]["output"];
  commitCount6Months: Scalars["Oso_Float32"]["output"];
  contributorCount: Scalars["Oso_Float32"]["output"];
  contributorCount6Months: Scalars["Oso_Float32"]["output"];
  eventSource: Scalars["String"]["output"];
  firstCommitDate: Scalars["Oso_DateTime"]["output"];
  forkCount: Scalars["Oso_Int64"]["output"];
  fulltimeDeveloperAverage6Months: Scalars["Oso_Float32"]["output"];
  lastCommitDate: Scalars["Oso_DateTime"]["output"];
  mergedPullRequestCount6Months: Scalars["Oso_Float32"]["output"];
  newContributorCount6Months: Scalars["Oso_Float32"]["output"];
  openedIssueCount6Months: Scalars["Oso_Float32"]["output"];
  openedPullRequestCount6Months: Scalars["Oso_Float32"]["output"];
  starCount: Scalars["Oso_Int64"]["output"];
};

export type Oso_CodeMetricsByArtifactV0BoolExp = {
  _and?: InputMaybe<Array<Oso_CodeMetricsByArtifactV0BoolExp>>;
  _not?: InputMaybe<Oso_CodeMetricsByArtifactV0BoolExp>;
  _or?: InputMaybe<Array<Oso_CodeMetricsByArtifactV0BoolExp>>;
  activeDeveloperCount6Months?: InputMaybe<Oso_Float32BoolExp>;
  artifactId?: InputMaybe<Oso_StringBoolExp>;
  artifactName?: InputMaybe<Oso_StringBoolExp>;
  artifactNamespace?: InputMaybe<Oso_StringBoolExp>;
  closedIssueCount6Months?: InputMaybe<Oso_Float32BoolExp>;
  commitCount6Months?: InputMaybe<Oso_Float32BoolExp>;
  contributorCount?: InputMaybe<Oso_Float32BoolExp>;
  contributorCount6Months?: InputMaybe<Oso_Float32BoolExp>;
  eventSource?: InputMaybe<Oso_StringBoolExp>;
  firstCommitDate?: InputMaybe<Oso_DateTimeBoolExp>;
  forkCount?: InputMaybe<Oso_Int64BoolExp>;
  fulltimeDeveloperAverage6Months?: InputMaybe<Oso_Float32BoolExp>;
  lastCommitDate?: InputMaybe<Oso_DateTimeBoolExp>;
  mergedPullRequestCount6Months?: InputMaybe<Oso_Float32BoolExp>;
  newContributorCount6Months?: InputMaybe<Oso_Float32BoolExp>;
  openedIssueCount6Months?: InputMaybe<Oso_Float32BoolExp>;
  openedPullRequestCount6Months?: InputMaybe<Oso_Float32BoolExp>;
  starCount?: InputMaybe<Oso_Int64BoolExp>;
};

export type Oso_CodeMetricsByArtifactV0OrderBy = {
  activeDeveloperCount6Months?: InputMaybe<OrderBy>;
  artifactId?: InputMaybe<OrderBy>;
  artifactName?: InputMaybe<OrderBy>;
  artifactNamespace?: InputMaybe<OrderBy>;
  closedIssueCount6Months?: InputMaybe<OrderBy>;
  commitCount6Months?: InputMaybe<OrderBy>;
  contributorCount?: InputMaybe<OrderBy>;
  contributorCount6Months?: InputMaybe<OrderBy>;
  eventSource?: InputMaybe<OrderBy>;
  firstCommitDate?: InputMaybe<OrderBy>;
  forkCount?: InputMaybe<OrderBy>;
  fulltimeDeveloperAverage6Months?: InputMaybe<OrderBy>;
  lastCommitDate?: InputMaybe<OrderBy>;
  mergedPullRequestCount6Months?: InputMaybe<OrderBy>;
  newContributorCount6Months?: InputMaybe<OrderBy>;
  openedIssueCount6Months?: InputMaybe<OrderBy>;
  openedPullRequestCount6Months?: InputMaybe<OrderBy>;
  starCount?: InputMaybe<OrderBy>;
};

export type Oso_CodeMetricsByProjectV1 = {
  __typename?: "Oso_CodeMetricsByProjectV1";
  activeDeveloperCount6Months: Scalars["Oso_Float32"]["output"];
  closedIssueCount6Months: Scalars["Oso_Float32"]["output"];
  commentCount6Months: Scalars["Oso_Float32"]["output"];
  commitCount6Months: Scalars["Oso_Float32"]["output"];
  contributorCount: Scalars["Oso_Float32"]["output"];
  contributorCount6Months: Scalars["Oso_Float32"]["output"];
  developerCount: Scalars["Oso_Float32"]["output"];
  displayName: Scalars["String"]["output"];
  eventSource: Scalars["String"]["output"];
  firstCommitDate: Scalars["Oso_DateTime"]["output"];
  firstCreatedAtDate: Scalars["Oso_DateTime"]["output"];
  forkCount: Scalars["Oso_Int64"]["output"];
  fulltimeDeveloperAverage6Months: Scalars["Oso_Float32"]["output"];
  lastCommitDate: Scalars["Oso_DateTime"]["output"];
  lastUpdatedAtDate: Scalars["Oso_DateTime"]["output"];
  mergedPullRequestCount6Months: Scalars["Oso_Float32"]["output"];
  newContributorCount6Months: Scalars["Oso_Float32"]["output"];
  openedIssueCount6Months: Scalars["Oso_Float32"]["output"];
  openedPullRequestCount6Months: Scalars["Oso_Float32"]["output"];
  projectId: Scalars["String"]["output"];
  projectName: Scalars["String"]["output"];
  projectNamespace: Scalars["String"]["output"];
  projectSource: Scalars["String"]["output"];
  releaseCount6Months: Scalars["Oso_Float32"]["output"];
  repositoryCount: Scalars["Oso_Int64"]["output"];
  starCount: Scalars["Oso_Int64"]["output"];
  timeToFirstResponseDaysAverage6Months: Scalars["Oso_Float32"]["output"];
  timeToMergeDaysAverage6Months: Scalars["Oso_Float32"]["output"];
};

export type Oso_CodeMetricsByProjectV1BoolExp = {
  _and?: InputMaybe<Array<Oso_CodeMetricsByProjectV1BoolExp>>;
  _not?: InputMaybe<Oso_CodeMetricsByProjectV1BoolExp>;
  _or?: InputMaybe<Array<Oso_CodeMetricsByProjectV1BoolExp>>;
  activeDeveloperCount6Months?: InputMaybe<Oso_Float32BoolExp>;
  closedIssueCount6Months?: InputMaybe<Oso_Float32BoolExp>;
  commentCount6Months?: InputMaybe<Oso_Float32BoolExp>;
  commitCount6Months?: InputMaybe<Oso_Float32BoolExp>;
  contributorCount?: InputMaybe<Oso_Float32BoolExp>;
  contributorCount6Months?: InputMaybe<Oso_Float32BoolExp>;
  developerCount?: InputMaybe<Oso_Float32BoolExp>;
  displayName?: InputMaybe<Oso_StringBoolExp>;
  eventSource?: InputMaybe<Oso_StringBoolExp>;
  firstCommitDate?: InputMaybe<Oso_DateTimeBoolExp>;
  firstCreatedAtDate?: InputMaybe<Oso_DateTimeBoolExp>;
  forkCount?: InputMaybe<Oso_Int64BoolExp>;
  fulltimeDeveloperAverage6Months?: InputMaybe<Oso_Float32BoolExp>;
  lastCommitDate?: InputMaybe<Oso_DateTimeBoolExp>;
  lastUpdatedAtDate?: InputMaybe<Oso_DateTimeBoolExp>;
  mergedPullRequestCount6Months?: InputMaybe<Oso_Float32BoolExp>;
  newContributorCount6Months?: InputMaybe<Oso_Float32BoolExp>;
  openedIssueCount6Months?: InputMaybe<Oso_Float32BoolExp>;
  openedPullRequestCount6Months?: InputMaybe<Oso_Float32BoolExp>;
  projectId?: InputMaybe<Oso_StringBoolExp>;
  projectName?: InputMaybe<Oso_StringBoolExp>;
  projectNamespace?: InputMaybe<Oso_StringBoolExp>;
  projectSource?: InputMaybe<Oso_StringBoolExp>;
  releaseCount6Months?: InputMaybe<Oso_Float32BoolExp>;
  repositoryCount?: InputMaybe<Oso_Int64BoolExp>;
  starCount?: InputMaybe<Oso_Int64BoolExp>;
  timeToFirstResponseDaysAverage6Months?: InputMaybe<Oso_Float32BoolExp>;
  timeToMergeDaysAverage6Months?: InputMaybe<Oso_Float32BoolExp>;
};

export type Oso_CodeMetricsByProjectV1OrderBy = {
  activeDeveloperCount6Months?: InputMaybe<OrderBy>;
  closedIssueCount6Months?: InputMaybe<OrderBy>;
  commentCount6Months?: InputMaybe<OrderBy>;
  commitCount6Months?: InputMaybe<OrderBy>;
  contributorCount?: InputMaybe<OrderBy>;
  contributorCount6Months?: InputMaybe<OrderBy>;
  developerCount?: InputMaybe<OrderBy>;
  displayName?: InputMaybe<OrderBy>;
  eventSource?: InputMaybe<OrderBy>;
  firstCommitDate?: InputMaybe<OrderBy>;
  firstCreatedAtDate?: InputMaybe<OrderBy>;
  forkCount?: InputMaybe<OrderBy>;
  fulltimeDeveloperAverage6Months?: InputMaybe<OrderBy>;
  lastCommitDate?: InputMaybe<OrderBy>;
  lastUpdatedAtDate?: InputMaybe<OrderBy>;
  mergedPullRequestCount6Months?: InputMaybe<OrderBy>;
  newContributorCount6Months?: InputMaybe<OrderBy>;
  openedIssueCount6Months?: InputMaybe<OrderBy>;
  openedPullRequestCount6Months?: InputMaybe<OrderBy>;
  projectId?: InputMaybe<OrderBy>;
  projectName?: InputMaybe<OrderBy>;
  projectNamespace?: InputMaybe<OrderBy>;
  projectSource?: InputMaybe<OrderBy>;
  releaseCount6Months?: InputMaybe<OrderBy>;
  repositoryCount?: InputMaybe<OrderBy>;
  starCount?: InputMaybe<OrderBy>;
  timeToFirstResponseDaysAverage6Months?: InputMaybe<OrderBy>;
  timeToMergeDaysAverage6Months?: InputMaybe<OrderBy>;
};

export type Oso_CollectionsV1 = {
  __typename?: "Oso_CollectionsV1";
  collectionId: Scalars["String"]["output"];
  collectionName: Scalars["String"]["output"];
  collectionNamespace: Scalars["String"]["output"];
  collectionSource: Scalars["String"]["output"];
  description: Scalars["String"]["output"];
  displayName: Scalars["String"]["output"];
};

export type Oso_CollectionsV1BoolExp = {
  _and?: InputMaybe<Array<Oso_CollectionsV1BoolExp>>;
  _not?: InputMaybe<Oso_CollectionsV1BoolExp>;
  _or?: InputMaybe<Array<Oso_CollectionsV1BoolExp>>;
  collectionId?: InputMaybe<Oso_StringBoolExp>;
  collectionName?: InputMaybe<Oso_StringBoolExp>;
  collectionNamespace?: InputMaybe<Oso_StringBoolExp>;
  collectionSource?: InputMaybe<Oso_StringBoolExp>;
  description?: InputMaybe<Oso_StringBoolExp>;
  displayName?: InputMaybe<Oso_StringBoolExp>;
};

export type Oso_CollectionsV1OrderBy = {
  collectionId?: InputMaybe<OrderBy>;
  collectionName?: InputMaybe<OrderBy>;
  collectionNamespace?: InputMaybe<OrderBy>;
  collectionSource?: InputMaybe<OrderBy>;
  description?: InputMaybe<OrderBy>;
  displayName?: InputMaybe<OrderBy>;
};

export type Oso_ContractsV0 = {
  __typename?: "Oso_ContractsV0";
  contractAddress: Scalars["String"]["output"];
  contractNamespace: Scalars["String"]["output"];
  deploymentDate: Scalars["Oso_Date"]["output"];
  factoryAddress: Scalars["String"]["output"];
  originatingAddress: Scalars["String"]["output"];
  rootDeployerAddress: Scalars["String"]["output"];
  sortWeight: Scalars["Oso_Int64"]["output"];
};

export type Oso_ContractsV0BoolExp = {
  _and?: InputMaybe<Array<Oso_ContractsV0BoolExp>>;
  _not?: InputMaybe<Oso_ContractsV0BoolExp>;
  _or?: InputMaybe<Array<Oso_ContractsV0BoolExp>>;
  contractAddress?: InputMaybe<Oso_StringBoolExp>;
  contractNamespace?: InputMaybe<Oso_StringBoolExp>;
  deploymentDate?: InputMaybe<Oso_DateBoolExp>;
  factoryAddress?: InputMaybe<Oso_StringBoolExp>;
  originatingAddress?: InputMaybe<Oso_StringBoolExp>;
  rootDeployerAddress?: InputMaybe<Oso_StringBoolExp>;
  sortWeight?: InputMaybe<Oso_Int64BoolExp>;
};

export type Oso_ContractsV0OrderByExp = {
  contractAddress?: InputMaybe<OrderBy>;
  contractNamespace?: InputMaybe<OrderBy>;
  deploymentDate?: InputMaybe<OrderBy>;
  factoryAddress?: InputMaybe<OrderBy>;
  originatingAddress?: InputMaybe<OrderBy>;
  rootDeployerAddress?: InputMaybe<OrderBy>;
  sortWeight?: InputMaybe<OrderBy>;
};

export type Oso_DateBoolExp = {
  _eq?: InputMaybe<Scalars["Oso_Date"]["input"]>;
  _gt?: InputMaybe<Scalars["Oso_Date"]["input"]>;
  _gte?: InputMaybe<Scalars["Oso_Date"]["input"]>;
  _in?: InputMaybe<Array<Scalars["Oso_Date"]["input"]>>;
  _is_null?: InputMaybe<Scalars["Boolean"]["input"]>;
  _lt?: InputMaybe<Scalars["Oso_Date"]["input"]>;
  _lte?: InputMaybe<Scalars["Oso_Date"]["input"]>;
  _neq?: InputMaybe<Scalars["Oso_Date"]["input"]>;
  _nin?: InputMaybe<Array<Scalars["Oso_Date"]["input"]>>;
};

export type Oso_DateTime646BoolExp = {
  _eq?: InputMaybe<Scalars["Oso_DateTime646"]["input"]>;
  _gt?: InputMaybe<Scalars["Oso_DateTime646"]["input"]>;
  _gte?: InputMaybe<Scalars["Oso_DateTime646"]["input"]>;
  _in?: InputMaybe<Array<Scalars["Oso_DateTime646"]["input"]>>;
  _is_null?: InputMaybe<Scalars["Boolean"]["input"]>;
  _lt?: InputMaybe<Scalars["Oso_DateTime646"]["input"]>;
  _lte?: InputMaybe<Scalars["Oso_DateTime646"]["input"]>;
  _neq?: InputMaybe<Scalars["Oso_DateTime646"]["input"]>;
  _nin?: InputMaybe<Array<Scalars["Oso_DateTime646"]["input"]>>;
};

export type Oso_DateTimeBoolExp = {
  _eq?: InputMaybe<Scalars["Oso_DateTime"]["input"]>;
  _gt?: InputMaybe<Scalars["Oso_DateTime"]["input"]>;
  _gte?: InputMaybe<Scalars["Oso_DateTime"]["input"]>;
  _in?: InputMaybe<Array<Scalars["Oso_DateTime"]["input"]>>;
  _is_null?: InputMaybe<Scalars["Boolean"]["input"]>;
  _lt?: InputMaybe<Scalars["Oso_DateTime"]["input"]>;
  _lte?: InputMaybe<Scalars["Oso_DateTime"]["input"]>;
  _neq?: InputMaybe<Scalars["Oso_DateTime"]["input"]>;
  _nin?: InputMaybe<Array<Scalars["Oso_DateTime"]["input"]>>;
};

export type Oso_EventTypesV1 = {
  __typename?: "Oso_EventTypesV1";
  eventType: Scalars["String"]["output"];
};

export type Oso_EventTypesV1BoolExp = {
  _and?: InputMaybe<Array<Oso_EventTypesV1BoolExp>>;
  _not?: InputMaybe<Oso_EventTypesV1BoolExp>;
  _or?: InputMaybe<Array<Oso_EventTypesV1BoolExp>>;
  eventType?: InputMaybe<Oso_StringBoolExp>;
};

export type Oso_EventTypesV1OrderBy = {
  eventType?: InputMaybe<OrderBy>;
};

export type Oso_Float32BoolExp = {
  _eq?: InputMaybe<Scalars["Oso_Float32"]["input"]>;
  _gt?: InputMaybe<Scalars["Oso_Float32"]["input"]>;
  _gte?: InputMaybe<Scalars["Oso_Float32"]["input"]>;
  _in?: InputMaybe<Array<Scalars["Oso_Float32"]["input"]>>;
  _is_null?: InputMaybe<Scalars["Boolean"]["input"]>;
  _lt?: InputMaybe<Scalars["Oso_Float32"]["input"]>;
  _lte?: InputMaybe<Scalars["Oso_Float32"]["input"]>;
  _neq?: InputMaybe<Scalars["Oso_Float32"]["input"]>;
  _nin?: InputMaybe<Array<Scalars["Oso_Float32"]["input"]>>;
};

export type Oso_Float64BoolExp = {
  _eq?: InputMaybe<Scalars["Oso_Float64"]["input"]>;
  _gt?: InputMaybe<Scalars["Oso_Float64"]["input"]>;
  _gte?: InputMaybe<Scalars["Oso_Float64"]["input"]>;
  _in?: InputMaybe<Array<Scalars["Oso_Float64"]["input"]>>;
  _is_null?: InputMaybe<Scalars["Boolean"]["input"]>;
  _lt?: InputMaybe<Scalars["Oso_Float64"]["input"]>;
  _lte?: InputMaybe<Scalars["Oso_Float64"]["input"]>;
  _neq?: InputMaybe<Scalars["Oso_Float64"]["input"]>;
  _nin?: InputMaybe<Array<Scalars["Oso_Float64"]["input"]>>;
};

export type Oso_FundingMetricsByProjectV1 = {
  __typename?: "Oso_FundingMetricsByProjectV1";
  displayName: Scalars["String"]["output"];
  eventSource: Scalars["String"]["output"];
  projectId: Scalars["String"]["output"];
  projectName: Scalars["String"]["output"];
  projectNamespace: Scalars["String"]["output"];
  projectSource: Scalars["String"]["output"];
  totalFundersCount: Scalars["Oso_Int64"]["output"];
  totalFundingReceivedUsd: Scalars["Oso_Float32"]["output"];
  totalFundingReceivedUsd6Months: Scalars["Oso_Float32"]["output"];
};

export type Oso_FundingMetricsByProjectV1BoolExp = {
  _and?: InputMaybe<Array<Oso_FundingMetricsByProjectV1BoolExp>>;
  _not?: InputMaybe<Oso_FundingMetricsByProjectV1BoolExp>;
  _or?: InputMaybe<Array<Oso_FundingMetricsByProjectV1BoolExp>>;
  displayName?: InputMaybe<Oso_StringBoolExp>;
  eventSource?: InputMaybe<Oso_StringBoolExp>;
  projectId?: InputMaybe<Oso_StringBoolExp>;
  projectName?: InputMaybe<Oso_StringBoolExp>;
  projectNamespace?: InputMaybe<Oso_StringBoolExp>;
  projectSource?: InputMaybe<Oso_StringBoolExp>;
  totalFundersCount?: InputMaybe<Oso_Int64BoolExp>;
  totalFundingReceivedUsd?: InputMaybe<Oso_Float32BoolExp>;
  totalFundingReceivedUsd6Months?: InputMaybe<Oso_Float32BoolExp>;
};

export type Oso_FundingMetricsByProjectV1OrderBy = {
  displayName?: InputMaybe<OrderBy>;
  eventSource?: InputMaybe<OrderBy>;
  projectId?: InputMaybe<OrderBy>;
  projectName?: InputMaybe<OrderBy>;
  projectNamespace?: InputMaybe<OrderBy>;
  projectSource?: InputMaybe<OrderBy>;
  totalFundersCount?: InputMaybe<OrderBy>;
  totalFundingReceivedUsd?: InputMaybe<OrderBy>;
  totalFundingReceivedUsd6Months?: InputMaybe<OrderBy>;
};

export type Oso_Int64BoolExp = {
  _eq?: InputMaybe<Scalars["Oso_Int64"]["input"]>;
  _gt?: InputMaybe<Scalars["Oso_Int64"]["input"]>;
  _gte?: InputMaybe<Scalars["Oso_Int64"]["input"]>;
  _in?: InputMaybe<Array<Scalars["Oso_Int64"]["input"]>>;
  _is_null?: InputMaybe<Scalars["Boolean"]["input"]>;
  _lt?: InputMaybe<Scalars["Oso_Int64"]["input"]>;
  _lte?: InputMaybe<Scalars["Oso_Int64"]["input"]>;
  _neq?: InputMaybe<Scalars["Oso_Int64"]["input"]>;
  _nin?: InputMaybe<Array<Scalars["Oso_Int64"]["input"]>>;
};

export type Oso_KeyMetricsByArtifactV0 = {
  __typename?: "Oso_KeyMetricsByArtifactV0";
  amount: Scalars["Oso_Float64"]["output"];
  artifactId: Scalars["String"]["output"];
  metricId: Scalars["String"]["output"];
  sampleDate: Scalars["Oso_Date"]["output"];
  unit: Scalars["String"]["output"];
};

export type Oso_KeyMetricsByArtifactV0BoolExp = {
  _and?: InputMaybe<Array<Oso_KeyMetricsByArtifactV0BoolExp>>;
  _not?: InputMaybe<Oso_KeyMetricsByArtifactV0BoolExp>;
  _or?: InputMaybe<Array<Oso_KeyMetricsByArtifactV0BoolExp>>;
  amount?: InputMaybe<Oso_Float64BoolExp>;
  artifactId?: InputMaybe<Oso_StringBoolExp>;
  metricId?: InputMaybe<Oso_StringBoolExp>;
  sampleDate?: InputMaybe<Oso_DateBoolExp>;
  unit?: InputMaybe<Oso_StringBoolExp>;
};

export type Oso_KeyMetricsByArtifactV0OrderByExp = {
  amount?: InputMaybe<OrderBy>;
  artifactId?: InputMaybe<OrderBy>;
  metricId?: InputMaybe<OrderBy>;
  sampleDate?: InputMaybe<OrderBy>;
  unit?: InputMaybe<OrderBy>;
};

export type Oso_KeyMetricsByCollectionV0 = {
  __typename?: "Oso_KeyMetricsByCollectionV0";
  amount: Scalars["Oso_Float64"]["output"];
  collectionId: Scalars["String"]["output"];
  metricId: Scalars["String"]["output"];
  sampleDate: Scalars["Oso_Date"]["output"];
  unit: Scalars["String"]["output"];
};

export type Oso_KeyMetricsByCollectionV0BoolExp = {
  _and?: InputMaybe<Array<Oso_KeyMetricsByCollectionV0BoolExp>>;
  _not?: InputMaybe<Oso_KeyMetricsByCollectionV0BoolExp>;
  _or?: InputMaybe<Array<Oso_KeyMetricsByCollectionV0BoolExp>>;
  amount?: InputMaybe<Oso_Float64BoolExp>;
  collectionId?: InputMaybe<Oso_StringBoolExp>;
  metricId?: InputMaybe<Oso_StringBoolExp>;
  sampleDate?: InputMaybe<Oso_DateBoolExp>;
  unit?: InputMaybe<Oso_StringBoolExp>;
};

export type Oso_KeyMetricsByCollectionV0OrderByExp = {
  amount?: InputMaybe<OrderBy>;
  collectionId?: InputMaybe<OrderBy>;
  metricId?: InputMaybe<OrderBy>;
  sampleDate?: InputMaybe<OrderBy>;
  unit?: InputMaybe<OrderBy>;
};

export type Oso_KeyMetricsByProjectV0 = {
  __typename?: "Oso_KeyMetricsByProjectV0";
  amount: Scalars["Oso_Float64"]["output"];
  metricId: Scalars["String"]["output"];
  projectId: Scalars["String"]["output"];
  sampleDate: Scalars["Oso_Date"]["output"];
  unit: Scalars["String"]["output"];
};

export type Oso_KeyMetricsByProjectV0BoolExp = {
  _and?: InputMaybe<Array<Oso_KeyMetricsByProjectV0BoolExp>>;
  _not?: InputMaybe<Oso_KeyMetricsByProjectV0BoolExp>;
  _or?: InputMaybe<Array<Oso_KeyMetricsByProjectV0BoolExp>>;
  amount?: InputMaybe<Oso_Float64BoolExp>;
  metricId?: InputMaybe<Oso_StringBoolExp>;
  projectId?: InputMaybe<Oso_StringBoolExp>;
  sampleDate?: InputMaybe<Oso_DateBoolExp>;
  unit?: InputMaybe<Oso_StringBoolExp>;
};

export type Oso_KeyMetricsByProjectV0OrderByExp = {
  amount?: InputMaybe<OrderBy>;
  metricId?: InputMaybe<OrderBy>;
  projectId?: InputMaybe<OrderBy>;
  sampleDate?: InputMaybe<OrderBy>;
  unit?: InputMaybe<OrderBy>;
};

export type Oso_MetricsV0 = {
  __typename?: "Oso_MetricsV0";
  aggregationFunction: Scalars["String"]["output"];
  definitionRef: Scalars["String"]["output"];
  description: Scalars["String"]["output"];
  displayName: Scalars["String"]["output"];
  metricId: Scalars["String"]["output"];
  metricName: Scalars["String"]["output"];
  metricNamespace: Scalars["String"]["output"];
  metricSource: Scalars["String"]["output"];
  rawDefinition: Scalars["String"]["output"];
};

export type Oso_MetricsV0BoolExp = {
  _and?: InputMaybe<Array<Oso_MetricsV0BoolExp>>;
  _not?: InputMaybe<Oso_MetricsV0BoolExp>;
  _or?: InputMaybe<Array<Oso_MetricsV0BoolExp>>;
  aggregationFunction?: InputMaybe<Oso_StringBoolExp>;
  definitionRef?: InputMaybe<Oso_StringBoolExp>;
  description?: InputMaybe<Oso_StringBoolExp>;
  displayName?: InputMaybe<Oso_StringBoolExp>;
  metricId?: InputMaybe<Oso_StringBoolExp>;
  metricName?: InputMaybe<Oso_StringBoolExp>;
  metricNamespace?: InputMaybe<Oso_StringBoolExp>;
  metricSource?: InputMaybe<Oso_StringBoolExp>;
  rawDefinition?: InputMaybe<Oso_StringBoolExp>;
};

export type Oso_MetricsV0OrderBy = {
  aggregationFunction?: InputMaybe<OrderBy>;
  definitionRef?: InputMaybe<OrderBy>;
  description?: InputMaybe<OrderBy>;
  displayName?: InputMaybe<OrderBy>;
  metricId?: InputMaybe<OrderBy>;
  metricName?: InputMaybe<OrderBy>;
  metricNamespace?: InputMaybe<OrderBy>;
  metricSource?: InputMaybe<OrderBy>;
  rawDefinition?: InputMaybe<OrderBy>;
};

export type Oso_ModelsV0 = {
  __typename?: "Oso_ModelsV0";
  modelId: Scalars["String"]["output"];
  modelName: Scalars["String"]["output"];
  renderedAt: Scalars["Oso_DateTime646"]["output"];
  renderedSql: Scalars["String"]["output"];
};

export type Oso_ModelsV0BoolExp = {
  _and?: InputMaybe<Array<Oso_ModelsV0BoolExp>>;
  _not?: InputMaybe<Oso_ModelsV0BoolExp>;
  _or?: InputMaybe<Array<Oso_ModelsV0BoolExp>>;
  modelId?: InputMaybe<Oso_StringBoolExp>;
  modelName?: InputMaybe<Oso_StringBoolExp>;
  renderedAt?: InputMaybe<Oso_DateTime646BoolExp>;
  renderedSql?: InputMaybe<Oso_StringBoolExp>;
};

export type Oso_ModelsV0OrderByExp = {
  modelId?: InputMaybe<OrderBy>;
  modelName?: InputMaybe<OrderBy>;
  renderedAt?: InputMaybe<OrderBy>;
  renderedSql?: InputMaybe<OrderBy>;
};

export type Oso_OnchainMetricsByProjectV1 = {
  __typename?: "Oso_OnchainMetricsByProjectV1";
  activeContractCount90Days: Scalars["Oso_Float32"]["output"];
  addressCount: Scalars["Oso_Float32"]["output"];
  addressCount90Days: Scalars["Oso_Float32"]["output"];
  daysSinceFirstTransaction: Scalars["Oso_Float32"]["output"];
  displayName: Scalars["String"]["output"];
  eventSource: Scalars["String"]["output"];
  gasFeesSum: Scalars["Oso_Float32"]["output"];
  gasFeesSum6Months: Scalars["Oso_Float32"]["output"];
  highActivityAddressCount90Days: Scalars["Oso_Float32"]["output"];
  lowActivityAddressCount90Days: Scalars["Oso_Float32"]["output"];
  mediumActivityAddressCount90Days: Scalars["Oso_Float32"]["output"];
  multiProjectAddressCount90Days: Scalars["Oso_Float32"]["output"];
  newAddressCount90Days: Scalars["Oso_Float32"]["output"];
  projectId: Scalars["String"]["output"];
  projectName: Scalars["String"]["output"];
  projectNamespace: Scalars["String"]["output"];
  projectSource: Scalars["String"]["output"];
  returningAddressCount90Days: Scalars["Oso_Float32"]["output"];
  transactionCount: Scalars["Oso_Float32"]["output"];
  transactionCount6Months: Scalars["Oso_Float32"]["output"];
};

export type Oso_OnchainMetricsByProjectV1BoolExp = {
  _and?: InputMaybe<Array<Oso_OnchainMetricsByProjectV1BoolExp>>;
  _not?: InputMaybe<Oso_OnchainMetricsByProjectV1BoolExp>;
  _or?: InputMaybe<Array<Oso_OnchainMetricsByProjectV1BoolExp>>;
  activeContractCount90Days?: InputMaybe<Oso_Float32BoolExp>;
  addressCount?: InputMaybe<Oso_Float32BoolExp>;
  addressCount90Days?: InputMaybe<Oso_Float32BoolExp>;
  daysSinceFirstTransaction?: InputMaybe<Oso_Float32BoolExp>;
  displayName?: InputMaybe<Oso_StringBoolExp>;
  eventSource?: InputMaybe<Oso_StringBoolExp>;
  gasFeesSum?: InputMaybe<Oso_Float32BoolExp>;
  gasFeesSum6Months?: InputMaybe<Oso_Float32BoolExp>;
  highActivityAddressCount90Days?: InputMaybe<Oso_Float32BoolExp>;
  lowActivityAddressCount90Days?: InputMaybe<Oso_Float32BoolExp>;
  mediumActivityAddressCount90Days?: InputMaybe<Oso_Float32BoolExp>;
  multiProjectAddressCount90Days?: InputMaybe<Oso_Float32BoolExp>;
  newAddressCount90Days?: InputMaybe<Oso_Float32BoolExp>;
  projectId?: InputMaybe<Oso_StringBoolExp>;
  projectName?: InputMaybe<Oso_StringBoolExp>;
  projectNamespace?: InputMaybe<Oso_StringBoolExp>;
  projectSource?: InputMaybe<Oso_StringBoolExp>;
  returningAddressCount90Days?: InputMaybe<Oso_Float32BoolExp>;
  transactionCount?: InputMaybe<Oso_Float32BoolExp>;
  transactionCount6Months?: InputMaybe<Oso_Float32BoolExp>;
};

export type Oso_OnchainMetricsByProjectV1OrderBy = {
  activeContractCount90Days?: InputMaybe<OrderBy>;
  addressCount?: InputMaybe<OrderBy>;
  addressCount90Days?: InputMaybe<OrderBy>;
  daysSinceFirstTransaction?: InputMaybe<OrderBy>;
  displayName?: InputMaybe<OrderBy>;
  eventSource?: InputMaybe<OrderBy>;
  gasFeesSum?: InputMaybe<OrderBy>;
  gasFeesSum6Months?: InputMaybe<OrderBy>;
  highActivityAddressCount90Days?: InputMaybe<OrderBy>;
  lowActivityAddressCount90Days?: InputMaybe<OrderBy>;
  mediumActivityAddressCount90Days?: InputMaybe<OrderBy>;
  multiProjectAddressCount90Days?: InputMaybe<OrderBy>;
  newAddressCount90Days?: InputMaybe<OrderBy>;
  projectId?: InputMaybe<OrderBy>;
  projectName?: InputMaybe<OrderBy>;
  projectNamespace?: InputMaybe<OrderBy>;
  projectSource?: InputMaybe<OrderBy>;
  returningAddressCount90Days?: InputMaybe<OrderBy>;
  transactionCount?: InputMaybe<OrderBy>;
  transactionCount6Months?: InputMaybe<OrderBy>;
};

export type Oso_PackageOwnersV0 = {
  __typename?: "Oso_PackageOwnersV0";
  packageArtifactId: Scalars["String"]["output"];
  packageArtifactName: Scalars["String"]["output"];
  packageArtifactNamespace: Scalars["String"]["output"];
  packageArtifactSource: Scalars["String"]["output"];
  packageOwnerArtifactId: Scalars["String"]["output"];
  packageOwnerArtifactName: Scalars["String"]["output"];
  packageOwnerArtifactNamespace: Scalars["String"]["output"];
  packageOwnerProjectId: Scalars["String"]["output"];
  packageOwnerSource: Scalars["String"]["output"];
  packageProjectId: Scalars["String"]["output"];
};

export type Oso_PackageOwnersV0BoolExp = {
  _and?: InputMaybe<Array<Oso_PackageOwnersV0BoolExp>>;
  _not?: InputMaybe<Oso_PackageOwnersV0BoolExp>;
  _or?: InputMaybe<Array<Oso_PackageOwnersV0BoolExp>>;
  packageArtifactId?: InputMaybe<Oso_StringBoolExp>;
  packageArtifactName?: InputMaybe<Oso_StringBoolExp>;
  packageArtifactNamespace?: InputMaybe<Oso_StringBoolExp>;
  packageArtifactSource?: InputMaybe<Oso_StringBoolExp>;
  packageOwnerArtifactId?: InputMaybe<Oso_StringBoolExp>;
  packageOwnerArtifactName?: InputMaybe<Oso_StringBoolExp>;
  packageOwnerArtifactNamespace?: InputMaybe<Oso_StringBoolExp>;
  packageOwnerProjectId?: InputMaybe<Oso_StringBoolExp>;
  packageOwnerSource?: InputMaybe<Oso_StringBoolExp>;
  packageProjectId?: InputMaybe<Oso_StringBoolExp>;
};

export type Oso_PackageOwnersV0OrderByExp = {
  packageArtifactId?: InputMaybe<OrderBy>;
  packageArtifactName?: InputMaybe<OrderBy>;
  packageArtifactNamespace?: InputMaybe<OrderBy>;
  packageArtifactSource?: InputMaybe<OrderBy>;
  packageOwnerArtifactId?: InputMaybe<OrderBy>;
  packageOwnerArtifactName?: InputMaybe<OrderBy>;
  packageOwnerArtifactNamespace?: InputMaybe<OrderBy>;
  packageOwnerProjectId?: InputMaybe<OrderBy>;
  packageOwnerSource?: InputMaybe<OrderBy>;
  packageProjectId?: InputMaybe<OrderBy>;
};

export type Oso_ProjectsByCollectionV1 = {
  __typename?: "Oso_ProjectsByCollectionV1";
  collectionId: Scalars["String"]["output"];
  collectionName: Scalars["String"]["output"];
  collectionNamespace: Scalars["String"]["output"];
  collectionSource: Scalars["String"]["output"];
  projectId: Scalars["String"]["output"];
  projectName: Scalars["String"]["output"];
  projectNamespace: Scalars["String"]["output"];
  projectSource: Scalars["String"]["output"];
};

export type Oso_ProjectsByCollectionV1BoolExp = {
  _and?: InputMaybe<Array<Oso_ProjectsByCollectionV1BoolExp>>;
  _not?: InputMaybe<Oso_ProjectsByCollectionV1BoolExp>;
  _or?: InputMaybe<Array<Oso_ProjectsByCollectionV1BoolExp>>;
  collectionId?: InputMaybe<Oso_StringBoolExp>;
  collectionName?: InputMaybe<Oso_StringBoolExp>;
  collectionNamespace?: InputMaybe<Oso_StringBoolExp>;
  collectionSource?: InputMaybe<Oso_StringBoolExp>;
  projectId?: InputMaybe<Oso_StringBoolExp>;
  projectName?: InputMaybe<Oso_StringBoolExp>;
  projectNamespace?: InputMaybe<Oso_StringBoolExp>;
  projectSource?: InputMaybe<Oso_StringBoolExp>;
};

export type Oso_ProjectsByCollectionV1OrderBy = {
  collectionId?: InputMaybe<OrderBy>;
  collectionName?: InputMaybe<OrderBy>;
  collectionNamespace?: InputMaybe<OrderBy>;
  collectionSource?: InputMaybe<OrderBy>;
  projectId?: InputMaybe<OrderBy>;
  projectName?: InputMaybe<OrderBy>;
  projectNamespace?: InputMaybe<OrderBy>;
  projectSource?: InputMaybe<OrderBy>;
};

export type Oso_ProjectsV1 = {
  __typename?: "Oso_ProjectsV1";
  description: Scalars["String"]["output"];
  displayName: Scalars["String"]["output"];
  projectId: Scalars["String"]["output"];
  projectName: Scalars["String"]["output"];
  projectNamespace: Scalars["String"]["output"];
  projectSource: Scalars["String"]["output"];
};

export type Oso_ProjectsV1BoolExp = {
  _and?: InputMaybe<Array<Oso_ProjectsV1BoolExp>>;
  _not?: InputMaybe<Oso_ProjectsV1BoolExp>;
  _or?: InputMaybe<Array<Oso_ProjectsV1BoolExp>>;
  description?: InputMaybe<Oso_StringBoolExp>;
  displayName?: InputMaybe<Oso_StringBoolExp>;
  projectId?: InputMaybe<Oso_StringBoolExp>;
  projectName?: InputMaybe<Oso_StringBoolExp>;
  projectNamespace?: InputMaybe<Oso_StringBoolExp>;
  projectSource?: InputMaybe<Oso_StringBoolExp>;
};

export type Oso_ProjectsV1OrderBy = {
  description?: InputMaybe<OrderBy>;
  displayName?: InputMaybe<OrderBy>;
  projectId?: InputMaybe<OrderBy>;
  projectName?: InputMaybe<OrderBy>;
  projectNamespace?: InputMaybe<OrderBy>;
  projectSource?: InputMaybe<OrderBy>;
};

export type Oso_RepositoriesV0 = {
  __typename?: "Oso_RepositoriesV0";
  artifactId: Scalars["String"]["output"];
  artifactName: Scalars["String"]["output"];
  artifactNamespace: Scalars["String"]["output"];
  artifactSource: Scalars["String"]["output"];
  artifactSourceId: Scalars["String"]["output"];
  artifactUrl: Scalars["String"]["output"];
  branch: Scalars["String"]["output"];
  createdAt: Scalars["Oso_DateTime"]["output"];
  forkCount: Scalars["Oso_Int64"]["output"];
  isFork: Scalars["Oso_Bool"]["output"];
  language: Scalars["String"]["output"];
  licenseName: Scalars["String"]["output"];
  licenseSpdxId: Scalars["String"]["output"];
  projectId: Scalars["String"]["output"];
  starCount: Scalars["Oso_Int64"]["output"];
  updatedAt: Scalars["Oso_DateTime"]["output"];
  watcherCount: Scalars["Oso_Int64"]["output"];
};

export type Oso_RepositoriesV0BoolExp = {
  _and?: InputMaybe<Array<Oso_RepositoriesV0BoolExp>>;
  _not?: InputMaybe<Oso_RepositoriesV0BoolExp>;
  _or?: InputMaybe<Array<Oso_RepositoriesV0BoolExp>>;
  artifactId?: InputMaybe<Oso_StringBoolExp>;
  artifactName?: InputMaybe<Oso_StringBoolExp>;
  artifactNamespace?: InputMaybe<Oso_StringBoolExp>;
  artifactSource?: InputMaybe<Oso_StringBoolExp>;
  artifactSourceId?: InputMaybe<Oso_StringBoolExp>;
  artifactUrl?: InputMaybe<Oso_StringBoolExp>;
  branch?: InputMaybe<Oso_StringBoolExp>;
  createdAt?: InputMaybe<Oso_DateTimeBoolExp>;
  forkCount?: InputMaybe<Oso_Int64BoolExp>;
  isFork?: InputMaybe<Oso_BoolBoolExp>;
  language?: InputMaybe<Oso_StringBoolExp>;
  licenseName?: InputMaybe<Oso_StringBoolExp>;
  licenseSpdxId?: InputMaybe<Oso_StringBoolExp>;
  projectId?: InputMaybe<Oso_StringBoolExp>;
  starCount?: InputMaybe<Oso_Int64BoolExp>;
  updatedAt?: InputMaybe<Oso_DateTimeBoolExp>;
  watcherCount?: InputMaybe<Oso_Int64BoolExp>;
};

export type Oso_RepositoriesV0OrderByExp = {
  artifactId?: InputMaybe<OrderBy>;
  artifactName?: InputMaybe<OrderBy>;
  artifactNamespace?: InputMaybe<OrderBy>;
  artifactSource?: InputMaybe<OrderBy>;
  artifactSourceId?: InputMaybe<OrderBy>;
  artifactUrl?: InputMaybe<OrderBy>;
  branch?: InputMaybe<OrderBy>;
  createdAt?: InputMaybe<OrderBy>;
  forkCount?: InputMaybe<OrderBy>;
  isFork?: InputMaybe<OrderBy>;
  language?: InputMaybe<OrderBy>;
  licenseName?: InputMaybe<OrderBy>;
  licenseSpdxId?: InputMaybe<OrderBy>;
  projectId?: InputMaybe<OrderBy>;
  starCount?: InputMaybe<OrderBy>;
  updatedAt?: InputMaybe<OrderBy>;
  watcherCount?: InputMaybe<OrderBy>;
};

export type Oso_SbomsV0 = {
  __typename?: "Oso_SbomsV0";
  fromArtifactId: Scalars["String"]["output"];
  fromArtifactName: Scalars["String"]["output"];
  fromArtifactNamespace: Scalars["String"]["output"];
  fromArtifactSource: Scalars["String"]["output"];
  fromProjectId: Scalars["String"]["output"];
  toPackageArtifactId: Scalars["String"]["output"];
  toPackageArtifactName: Scalars["String"]["output"];
  toPackageArtifactNamespace: Scalars["String"]["output"];
  toPackageArtifactSource: Scalars["String"]["output"];
  toPackageProjectId: Scalars["String"]["output"];
};

export type Oso_SbomsV0BoolExp = {
  _and?: InputMaybe<Array<Oso_SbomsV0BoolExp>>;
  _not?: InputMaybe<Oso_SbomsV0BoolExp>;
  _or?: InputMaybe<Array<Oso_SbomsV0BoolExp>>;
  fromArtifactId?: InputMaybe<Oso_StringBoolExp>;
  fromArtifactName?: InputMaybe<Oso_StringBoolExp>;
  fromArtifactNamespace?: InputMaybe<Oso_StringBoolExp>;
  fromArtifactSource?: InputMaybe<Oso_StringBoolExp>;
  fromProjectId?: InputMaybe<Oso_StringBoolExp>;
  toPackageArtifactId?: InputMaybe<Oso_StringBoolExp>;
  toPackageArtifactName?: InputMaybe<Oso_StringBoolExp>;
  toPackageArtifactNamespace?: InputMaybe<Oso_StringBoolExp>;
  toPackageArtifactSource?: InputMaybe<Oso_StringBoolExp>;
  toPackageProjectId?: InputMaybe<Oso_StringBoolExp>;
};

export type Oso_SbomsV0OrderByExp = {
  fromArtifactId?: InputMaybe<OrderBy>;
  fromArtifactName?: InputMaybe<OrderBy>;
  fromArtifactNamespace?: InputMaybe<OrderBy>;
  fromArtifactSource?: InputMaybe<OrderBy>;
  fromProjectId?: InputMaybe<OrderBy>;
  toPackageArtifactId?: InputMaybe<OrderBy>;
  toPackageArtifactName?: InputMaybe<OrderBy>;
  toPackageArtifactNamespace?: InputMaybe<OrderBy>;
  toPackageArtifactSource?: InputMaybe<OrderBy>;
  toPackageProjectId?: InputMaybe<OrderBy>;
};

export type Oso_StringBoolExp = {
  _eq?: InputMaybe<Scalars["String"]["input"]>;
  _gt?: InputMaybe<Scalars["String"]["input"]>;
  _gte?: InputMaybe<Scalars["String"]["input"]>;
  _ilike?: InputMaybe<Scalars["String"]["input"]>;
  _in?: InputMaybe<Array<Scalars["String"]["input"]>>;
  _is_null?: InputMaybe<Scalars["Boolean"]["input"]>;
  _like?: InputMaybe<Scalars["String"]["input"]>;
  _lt?: InputMaybe<Scalars["String"]["input"]>;
  _lte?: InputMaybe<Scalars["String"]["input"]>;
  _match?: InputMaybe<Scalars["String"]["input"]>;
  _neq?: InputMaybe<Scalars["String"]["input"]>;
  _nilike?: InputMaybe<Scalars["String"]["input"]>;
  _nin?: InputMaybe<Array<Scalars["String"]["input"]>>;
  _nlike?: InputMaybe<Scalars["String"]["input"]>;
};

export type Oso_TimeseriesEventsByArtifactV0 = {
  __typename?: "Oso_TimeseriesEventsByArtifactV0";
  amount: Scalars["Oso_Float32"]["output"];
  eventSource: Scalars["String"]["output"];
  eventSourceId: Scalars["String"]["output"];
  eventType: Scalars["String"]["output"];
  fromArtifactId: Scalars["String"]["output"];
  time: Scalars["Oso_DateTime"]["output"];
  toArtifactId: Scalars["String"]["output"];
};

export type Oso_TimeseriesEventsByArtifactV0BoolExp = {
  _and?: InputMaybe<Array<Oso_TimeseriesEventsByArtifactV0BoolExp>>;
  _not?: InputMaybe<Oso_TimeseriesEventsByArtifactV0BoolExp>;
  _or?: InputMaybe<Array<Oso_TimeseriesEventsByArtifactV0BoolExp>>;
  amount?: InputMaybe<Oso_Float32BoolExp>;
  eventSource?: InputMaybe<Oso_StringBoolExp>;
  eventSourceId?: InputMaybe<Oso_StringBoolExp>;
  eventType?: InputMaybe<Oso_StringBoolExp>;
  fromArtifactId?: InputMaybe<Oso_StringBoolExp>;
  time?: InputMaybe<Oso_DateTimeBoolExp>;
  toArtifactId?: InputMaybe<Oso_StringBoolExp>;
};

export type Oso_TimeseriesEventsByArtifactV0OrderBy = {
  amount?: InputMaybe<OrderBy>;
  eventSource?: InputMaybe<OrderBy>;
  eventSourceId?: InputMaybe<OrderBy>;
  eventType?: InputMaybe<OrderBy>;
  fromArtifactId?: InputMaybe<OrderBy>;
  time?: InputMaybe<OrderBy>;
  toArtifactId?: InputMaybe<OrderBy>;
};

export type Oso_TimeseriesMetricsByArtifactV0 = {
  __typename?: "Oso_TimeseriesMetricsByArtifactV0";
  amount: Scalars["Oso_Float64"]["output"];
  artifactId: Scalars["String"]["output"];
  metricId: Scalars["String"]["output"];
  sampleDate: Scalars["Oso_Date"]["output"];
  unit: Scalars["String"]["output"];
};

export type Oso_TimeseriesMetricsByArtifactV0BoolExp = {
  _and?: InputMaybe<Array<Oso_TimeseriesMetricsByArtifactV0BoolExp>>;
  _not?: InputMaybe<Oso_TimeseriesMetricsByArtifactV0BoolExp>;
  _or?: InputMaybe<Array<Oso_TimeseriesMetricsByArtifactV0BoolExp>>;
  amount?: InputMaybe<Oso_Float64BoolExp>;
  artifactId?: InputMaybe<Oso_StringBoolExp>;
  metricId?: InputMaybe<Oso_StringBoolExp>;
  sampleDate?: InputMaybe<Oso_DateBoolExp>;
  unit?: InputMaybe<Oso_StringBoolExp>;
};

export type Oso_TimeseriesMetricsByArtifactV0OrderBy = {
  amount?: InputMaybe<OrderBy>;
  artifactId?: InputMaybe<OrderBy>;
  metricId?: InputMaybe<OrderBy>;
  sampleDate?: InputMaybe<OrderBy>;
  unit?: InputMaybe<OrderBy>;
};

export type Oso_TimeseriesMetricsByCollectionV0 = {
  __typename?: "Oso_TimeseriesMetricsByCollectionV0";
  amount: Scalars["Oso_Float64"]["output"];
  collectionId: Scalars["String"]["output"];
  metricId: Scalars["String"]["output"];
  sampleDate: Scalars["Oso_Date"]["output"];
  unit: Scalars["String"]["output"];
};

export type Oso_TimeseriesMetricsByCollectionV0BoolExp = {
  _and?: InputMaybe<Array<Oso_TimeseriesMetricsByCollectionV0BoolExp>>;
  _not?: InputMaybe<Oso_TimeseriesMetricsByCollectionV0BoolExp>;
  _or?: InputMaybe<Array<Oso_TimeseriesMetricsByCollectionV0BoolExp>>;
  amount?: InputMaybe<Oso_Float64BoolExp>;
  collectionId?: InputMaybe<Oso_StringBoolExp>;
  metricId?: InputMaybe<Oso_StringBoolExp>;
  sampleDate?: InputMaybe<Oso_DateBoolExp>;
  unit?: InputMaybe<Oso_StringBoolExp>;
};

export type Oso_TimeseriesMetricsByCollectionV0OrderBy = {
  amount?: InputMaybe<OrderBy>;
  collectionId?: InputMaybe<OrderBy>;
  metricId?: InputMaybe<OrderBy>;
  sampleDate?: InputMaybe<OrderBy>;
  unit?: InputMaybe<OrderBy>;
};

export type Oso_TimeseriesMetricsByProjectV0 = {
  __typename?: "Oso_TimeseriesMetricsByProjectV0";
  amount: Scalars["Oso_Float64"]["output"];
  metricId: Scalars["String"]["output"];
  projectId: Scalars["String"]["output"];
  sampleDate: Scalars["Oso_Date"]["output"];
  unit: Scalars["String"]["output"];
};

export type Oso_TimeseriesMetricsByProjectV0BoolExp = {
  _and?: InputMaybe<Array<Oso_TimeseriesMetricsByProjectV0BoolExp>>;
  _not?: InputMaybe<Oso_TimeseriesMetricsByProjectV0BoolExp>;
  _or?: InputMaybe<Array<Oso_TimeseriesMetricsByProjectV0BoolExp>>;
  amount?: InputMaybe<Oso_Float64BoolExp>;
  metricId?: InputMaybe<Oso_StringBoolExp>;
  projectId?: InputMaybe<Oso_StringBoolExp>;
  sampleDate?: InputMaybe<Oso_DateBoolExp>;
  unit?: InputMaybe<Oso_StringBoolExp>;
};

export type Oso_TimeseriesMetricsByProjectV0OrderBy = {
  amount?: InputMaybe<OrderBy>;
  metricId?: InputMaybe<OrderBy>;
  projectId?: InputMaybe<OrderBy>;
  sampleDate?: InputMaybe<OrderBy>;
  unit?: InputMaybe<OrderBy>;
};

export type Oso_UsersV1 = {
  __typename?: "Oso_UsersV1";
  bio: Scalars["String"]["output"];
  displayName: Scalars["String"]["output"];
  profilePictureUrl: Scalars["String"]["output"];
  url: Scalars["String"]["output"];
  userId: Scalars["String"]["output"];
  userSource: Scalars["String"]["output"];
  userSourceId: Scalars["String"]["output"];
};

export type Oso_UsersV1BoolExp = {
  _and?: InputMaybe<Array<Oso_UsersV1BoolExp>>;
  _not?: InputMaybe<Oso_UsersV1BoolExp>;
  _or?: InputMaybe<Array<Oso_UsersV1BoolExp>>;
  bio?: InputMaybe<Oso_StringBoolExp>;
  displayName?: InputMaybe<Oso_StringBoolExp>;
  profilePictureUrl?: InputMaybe<Oso_StringBoolExp>;
  url?: InputMaybe<Oso_StringBoolExp>;
  userId?: InputMaybe<Oso_StringBoolExp>;
  userSource?: InputMaybe<Oso_StringBoolExp>;
  userSourceId?: InputMaybe<Oso_StringBoolExp>;
};

export type Oso_UsersV1OrderBy = {
  bio?: InputMaybe<OrderBy>;
  displayName?: InputMaybe<OrderBy>;
  profilePictureUrl?: InputMaybe<OrderBy>;
  url?: InputMaybe<OrderBy>;
  userId?: InputMaybe<OrderBy>;
  userSource?: InputMaybe<OrderBy>;
  userSourceId?: InputMaybe<OrderBy>;
};

export type Output = {
  __typename?: "Output";
  definition: OutputDefinition;
  dependedBy: Array<Input>;
  solid: Solid;
};

export type OutputDefinition = {
  __typename?: "OutputDefinition";
  description?: Maybe<Scalars["String"]["output"]>;
  isDynamic?: Maybe<Scalars["Boolean"]["output"]>;
  metadataEntries: Array<MetadataEntry>;
  name: Scalars["String"]["output"];
  type: DagsterType;
};

export type OutputMapping = {
  __typename?: "OutputMapping";
  definition: OutputDefinition;
  mappedOutput: Output;
};

export type ParentMaterializedRuleEvaluationData = {
  __typename?: "ParentMaterializedRuleEvaluationData";
  updatedAssetKeys?: Maybe<Array<AssetKey>>;
  willUpdateAssetKeys?: Maybe<Array<AssetKey>>;
};

export type Partition = {
  __typename?: "Partition";
  mode: Scalars["String"]["output"];
  name: Scalars["String"]["output"];
  partitionSetName: Scalars["String"]["output"];
  runConfigOrError: PartitionRunConfigOrError;
  runs: Array<Run>;
  solidSelection?: Maybe<Array<Scalars["String"]["output"]>>;
  status?: Maybe<RunStatus>;
  tagsOrError: PartitionTagsOrError;
};

export type PartitionRunsArgs = {
  cursor?: InputMaybe<Scalars["String"]["input"]>;
  filter?: InputMaybe<RunsFilter>;
  limit?: InputMaybe<Scalars["Int"]["input"]>;
};

export type PartitionBackfill = RunsFeedEntry & {
  __typename?: "PartitionBackfill";
  assetBackfillData?: Maybe<AssetBackfillData>;
  assetCheckSelection?: Maybe<Array<AssetCheckhandle>>;
  assetSelection?: Maybe<Array<AssetKey>>;
  cancelableRuns: Array<Run>;
  creationTime: Scalars["Float"]["output"];
  description?: Maybe<Scalars["String"]["output"]>;
  /** Included to comply with RunsFeedEntry interface. Duplicate of endTimestamp. */
  endTime?: Maybe<Scalars["Float"]["output"]>;
  endTimestamp?: Maybe<Scalars["Float"]["output"]>;
  error?: Maybe<PythonError>;
  fromFailure: Scalars["Boolean"]["output"];
  hasCancelPermission: Scalars["Boolean"]["output"];
  hasResumePermission: Scalars["Boolean"]["output"];
  id: Scalars["ID"]["output"];
  isAssetBackfill: Scalars["Boolean"]["output"];
  isValidSerialization: Scalars["Boolean"]["output"];
  /** Included to comply with RunsFeedEntry interface. */
  jobName?: Maybe<Scalars["String"]["output"]>;
  logEvents: InstigationEventConnection;
  numCancelable: Scalars["Int"]["output"];
  numPartitions?: Maybe<Scalars["Int"]["output"]>;
  partitionNames?: Maybe<Array<Scalars["String"]["output"]>>;
  partitionSet?: Maybe<PartitionSet>;
  partitionSetName?: Maybe<Scalars["String"]["output"]>;
  partitionStatusCounts: Array<PartitionStatusCounts>;
  partitionStatuses?: Maybe<PartitionStatuses>;
  partitionsTargetedForAssetKey?: Maybe<AssetBackfillTargetPartitions>;
  reexecutionSteps?: Maybe<Array<Scalars["String"]["output"]>>;
  runStatus: RunStatus;
  runs: Array<Run>;
  /** Included to comply with RunsFeedEntry interface. Duplicate of timestamp. */
  startTime?: Maybe<Scalars["Float"]["output"]>;
  status: BulkActionStatus;
  tags: Array<PipelineTag>;
  timestamp: Scalars["Float"]["output"];
  title?: Maybe<Scalars["String"]["output"]>;
  unfinishedRuns: Array<Run>;
  user?: Maybe<Scalars["String"]["output"]>;
};

export type PartitionBackfillCancelableRunsArgs = {
  limit?: InputMaybe<Scalars["Int"]["input"]>;
};

export type PartitionBackfillLogEventsArgs = {
  cursor?: InputMaybe<Scalars["String"]["input"]>;
};

export type PartitionBackfillPartitionsTargetedForAssetKeyArgs = {
  assetKey?: InputMaybe<AssetKeyInput>;
};

export type PartitionBackfillRunsArgs = {
  limit?: InputMaybe<Scalars["Int"]["input"]>;
};

export type PartitionBackfillUnfinishedRunsArgs = {
  limit?: InputMaybe<Scalars["Int"]["input"]>;
};

export type PartitionBackfillOrError =
  | BackfillNotFoundError
  | PartitionBackfill
  | PythonError;

export type PartitionBackfills = {
  __typename?: "PartitionBackfills";
  results: Array<PartitionBackfill>;
};

export type PartitionBackfillsOrError = PartitionBackfills | PythonError;

export type PartitionDefinition = {
  __typename?: "PartitionDefinition";
  description: Scalars["String"]["output"];
  dimensionTypes: Array<DimensionDefinitionType>;
  fmt?: Maybe<Scalars["String"]["output"]>;
  name?: Maybe<Scalars["String"]["output"]>;
  type: PartitionDefinitionType;
};

export enum PartitionDefinitionType {
  Dynamic = "DYNAMIC",
  Multipartitioned = "MULTIPARTITIONED",
  Static = "STATIC",
  TimeWindow = "TIME_WINDOW",
}

export type PartitionKeyRange = {
  __typename?: "PartitionKeyRange";
  end: Scalars["String"]["output"];
  start: Scalars["String"]["output"];
};

export type PartitionKeys = {
  __typename?: "PartitionKeys";
  partitionKeys: Array<Scalars["String"]["output"]>;
};

export type PartitionKeysNotFoundError = Error & {
  __typename?: "PartitionKeysNotFoundError";
  message: Scalars["String"]["output"];
  partitionKeys: Array<Scalars["String"]["output"]>;
};

export type PartitionKeysOrError =
  | PartitionKeys
  | PartitionSubsetDeserializationError;

export type PartitionMapping = {
  __typename?: "PartitionMapping";
  className: Scalars["String"]["output"];
  description: Scalars["String"]["output"];
};

export type PartitionRange = {
  __typename?: "PartitionRange";
  end: Scalars["String"]["output"];
  start: Scalars["String"]["output"];
};

/** This type represents a partition range selection with start and end. */
export type PartitionRangeSelector = {
  end: Scalars["String"]["input"];
  start: Scalars["String"]["input"];
};

/** An enumeration. */
export enum PartitionRangeStatus {
  Failed = "FAILED",
  Materialized = "MATERIALIZED",
  Materializing = "MATERIALIZING",
}

export type PartitionRun = {
  __typename?: "PartitionRun";
  id: Scalars["String"]["output"];
  partitionName: Scalars["String"]["output"];
  run?: Maybe<Run>;
};

export type PartitionRunConfig = {
  __typename?: "PartitionRunConfig";
  yaml: Scalars["String"]["output"];
};

export type PartitionRunConfigOrError = PartitionRunConfig | PythonError;

export type PartitionSet = {
  __typename?: "PartitionSet";
  backfills: Array<PartitionBackfill>;
  id: Scalars["ID"]["output"];
  mode: Scalars["String"]["output"];
  name: Scalars["String"]["output"];
  partition?: Maybe<Partition>;
  partitionRuns: Array<PartitionRun>;
  partitionStatusesOrError: PartitionStatusesOrError;
  partitionsOrError: PartitionsOrError;
  pipelineName: Scalars["String"]["output"];
  repositoryOrigin: RepositoryOrigin;
  solidSelection?: Maybe<Array<Scalars["String"]["output"]>>;
};

export type PartitionSetBackfillsArgs = {
  cursor?: InputMaybe<Scalars["String"]["input"]>;
  limit?: InputMaybe<Scalars["Int"]["input"]>;
};

export type PartitionSetPartitionArgs = {
  partitionName: Scalars["String"]["input"];
};

export type PartitionSetPartitionsOrErrorArgs = {
  cursor?: InputMaybe<Scalars["String"]["input"]>;
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  reverse?: InputMaybe<Scalars["Boolean"]["input"]>;
};

export type PartitionSetNotFoundError = Error & {
  __typename?: "PartitionSetNotFoundError";
  message: Scalars["String"]["output"];
  partitionSetName: Scalars["String"]["output"];
};

export type PartitionSetOrError =
  | PartitionSet
  | PartitionSetNotFoundError
  | PythonError;

/**
 * This type represents the fields necessary to identify a
 *         pipeline or pipeline subset.
 */
export type PartitionSetSelector = {
  partitionSetName: Scalars["String"]["input"];
  repositorySelector: RepositorySelector;
};

export type PartitionSets = {
  __typename?: "PartitionSets";
  results: Array<PartitionSet>;
};

export type PartitionSetsOrError =
  | PartitionSets
  | PipelineNotFoundError
  | PythonError;

export type PartitionStats = {
  __typename?: "PartitionStats";
  numFailed: Scalars["Int"]["output"];
  numMaterialized: Scalars["Int"]["output"];
  numMaterializing: Scalars["Int"]["output"];
  numPartitions: Scalars["Int"]["output"];
};

export type PartitionStatus = {
  __typename?: "PartitionStatus";
  id: Scalars["String"]["output"];
  partitionName: Scalars["String"]["output"];
  runDuration?: Maybe<Scalars["Float"]["output"]>;
  runId?: Maybe<Scalars["String"]["output"]>;
  runStatus?: Maybe<RunStatus>;
};

export type PartitionStatus1D =
  | DefaultPartitionStatuses
  | TimePartitionStatuses;

export type PartitionStatusCounts = {
  __typename?: "PartitionStatusCounts";
  count: Scalars["Int"]["output"];
  runStatus: RunStatus;
};

export type PartitionStatuses = {
  __typename?: "PartitionStatuses";
  results: Array<PartitionStatus>;
};

export type PartitionStatusesOrError = PartitionStatuses | PythonError;

export type PartitionSubsetDeserializationError = Error & {
  __typename?: "PartitionSubsetDeserializationError";
  message: Scalars["String"]["output"];
};

export type PartitionTags = {
  __typename?: "PartitionTags";
  results: Array<PipelineTag>;
};

export type PartitionTagsAndConfig = {
  __typename?: "PartitionTagsAndConfig";
  jobName: Scalars["String"]["output"];
  name: Scalars["String"]["output"];
  runConfigOrError: PartitionRunConfigOrError;
  tagsOrError: PartitionTagsOrError;
};

export type PartitionTagsOrError = PartitionTags | PythonError;

export type PartitionedAssetConditionEvaluationNode = {
  __typename?: "PartitionedAssetConditionEvaluationNode";
  childUniqueIds: Array<Scalars["String"]["output"]>;
  description: Scalars["String"]["output"];
  endTimestamp?: Maybe<Scalars["Float"]["output"]>;
  numCandidates?: Maybe<Scalars["Int"]["output"]>;
  numTrue: Scalars["Int"]["output"];
  startTimestamp?: Maybe<Scalars["Float"]["output"]>;
  uniqueId: Scalars["String"]["output"];
};

export type Partitions = {
  __typename?: "Partitions";
  results: Array<Partition>;
};

/** This type represents a partitions selection for an asset. */
export type PartitionsByAssetSelector = {
  assetKey: AssetKeyInput;
  partitions?: InputMaybe<PartitionsSelector>;
};

export type PartitionsOrError = Partitions | PythonError;

/** This type represents a partitions selection. */
export type PartitionsSelector = {
  range?: InputMaybe<PartitionRangeSelector>;
  ranges?: InputMaybe<Array<PartitionRangeSelector>>;
};

export type PathMetadataEntry = MetadataEntry & {
  __typename?: "PathMetadataEntry";
  description?: Maybe<Scalars["String"]["output"]>;
  label: Scalars["String"]["output"];
  path: Scalars["String"]["output"];
};

export type PendingConcurrencyStep = {
  __typename?: "PendingConcurrencyStep";
  assignedTimestamp?: Maybe<Scalars["Float"]["output"]>;
  enqueuedTimestamp: Scalars["Float"]["output"];
  priority?: Maybe<Scalars["Int"]["output"]>;
  runId: Scalars["String"]["output"];
  stepKey: Scalars["String"]["output"];
};

export type Permission = {
  __typename?: "Permission";
  disabledReason?: Maybe<Scalars["String"]["output"]>;
  permission: Scalars["String"]["output"];
  value: Scalars["Boolean"]["output"];
};

export type Pipeline = IPipelineSnapshot &
  SolidContainer & {
    __typename?: "Pipeline";
    dagsterTypeOrError: DagsterTypeOrError;
    dagsterTypes: Array<DagsterType>;
    description?: Maybe<Scalars["String"]["output"]>;
    graphName: Scalars["String"]["output"];
    id: Scalars["ID"]["output"];
    isAssetJob: Scalars["Boolean"]["output"];
    isJob: Scalars["Boolean"]["output"];
    metadataEntries: Array<MetadataEntry>;
    modes: Array<Mode>;
    name: Scalars["String"]["output"];
    parentSnapshotId?: Maybe<Scalars["String"]["output"]>;
    partition?: Maybe<PartitionTagsAndConfig>;
    partitionKeysOrError: PartitionKeys;
    pipelineSnapshotId: Scalars["String"]["output"];
    presets: Array<PipelinePreset>;
    repository: Repository;
    runTags: Array<PipelineTag>;
    runs: Array<Run>;
    schedules: Array<Schedule>;
    sensors: Array<Sensor>;
    solidHandle?: Maybe<SolidHandle>;
    solidHandles: Array<SolidHandle>;
    solids: Array<Solid>;
    tags: Array<PipelineTag>;
  };

export type PipelineDagsterTypeOrErrorArgs = {
  dagsterTypeName: Scalars["String"]["input"];
};

export type PipelinePartitionArgs = {
  partitionName: Scalars["String"]["input"];
  selectedAssetKeys?: InputMaybe<Array<AssetKeyInput>>;
};

export type PipelinePartitionKeysOrErrorArgs = {
  cursor?: InputMaybe<Scalars["String"]["input"]>;
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  reverse?: InputMaybe<Scalars["Boolean"]["input"]>;
  selectedAssetKeys?: InputMaybe<Array<AssetKeyInput>>;
};

export type PipelineRunsArgs = {
  cursor?: InputMaybe<Scalars["String"]["input"]>;
  limit?: InputMaybe<Scalars["Int"]["input"]>;
};

export type PipelineSolidHandleArgs = {
  handleID: Scalars["String"]["input"];
};

export type PipelineSolidHandlesArgs = {
  parentHandleID?: InputMaybe<Scalars["String"]["input"]>;
};

export type PipelineConfigValidationError = {
  message: Scalars["String"]["output"];
  path: Array<Scalars["String"]["output"]>;
  reason: EvaluationErrorReason;
  stack: EvaluationStack;
};

export type PipelineConfigValidationInvalid = {
  errors: Array<PipelineConfigValidationError>;
  pipelineName: Scalars["String"]["output"];
};

export type PipelineConfigValidationResult =
  | InvalidSubsetError
  | PipelineConfigValidationValid
  | PipelineNotFoundError
  | PythonError
  | RunConfigValidationInvalid;

export type PipelineConfigValidationValid = {
  __typename?: "PipelineConfigValidationValid";
  pipelineName: Scalars["String"]["output"];
};

export type PipelineNotFoundError = Error & {
  __typename?: "PipelineNotFoundError";
  message: Scalars["String"]["output"];
  pipelineName: Scalars["String"]["output"];
  repositoryLocationName: Scalars["String"]["output"];
  repositoryName: Scalars["String"]["output"];
};

export type PipelineOrError =
  | InvalidSubsetError
  | Pipeline
  | PipelineNotFoundError
  | PythonError;

export type PipelinePreset = {
  __typename?: "PipelinePreset";
  mode: Scalars["String"]["output"];
  name: Scalars["String"]["output"];
  runConfigYaml: Scalars["String"]["output"];
  solidSelection?: Maybe<Array<Scalars["String"]["output"]>>;
  tags: Array<PipelineTag>;
};

/**
 * This interface supports the case where we can look up a pipeline successfully in the
 * repository available to the DagsterInstance/graphql context, as well as the case where we know
 * that a pipeline exists/existed thanks to materialized data such as logs and run metadata, but
 * where we can't look the concrete pipeline up.
 */
export type PipelineReference = {
  name: Scalars["String"]["output"];
  solidSelection?: Maybe<Array<Scalars["String"]["output"]>>;
};

export type PipelineRun = {
  assets: Array<Asset>;
  canTerminate: Scalars["Boolean"]["output"];
  /**
   *
   *         Captured logs are the stdout/stderr logs for a given file key within the run
   *
   */
  capturedLogs: CapturedLogs;
  eventConnection: EventConnection;
  executionPlan?: Maybe<ExecutionPlan>;
  id: Scalars["ID"]["output"];
  jobName: Scalars["String"]["output"];
  mode: Scalars["String"]["output"];
  parentRunId?: Maybe<Scalars["String"]["output"]>;
  pipeline: PipelineReference;
  pipelineName: Scalars["String"]["output"];
  pipelineSnapshotId?: Maybe<Scalars["String"]["output"]>;
  repositoryOrigin?: Maybe<RepositoryOrigin>;
  rootRunId?: Maybe<Scalars["String"]["output"]>;
  runConfig: Scalars["RunConfigData"]["output"];
  runConfigYaml: Scalars["String"]["output"];
  runId: Scalars["String"]["output"];
  solidSelection?: Maybe<Array<Scalars["String"]["output"]>>;
  stats: RunStatsSnapshotOrError;
  status: RunStatus;
  stepKeysToExecute?: Maybe<Array<Scalars["String"]["output"]>>;
  stepStats: Array<RunStepStats>;
  tags: Array<PipelineTag>;
};

export type PipelineRunCapturedLogsArgs = {
  fileKey: Scalars["String"]["input"];
};

export type PipelineRunEventConnectionArgs = {
  afterCursor?: InputMaybe<Scalars["String"]["input"]>;
  limit?: InputMaybe<Scalars["Int"]["input"]>;
};

export type PipelineRunConflict = {
  message: Scalars["String"]["output"];
};

export type PipelineRunLogsSubscriptionFailure = {
  __typename?: "PipelineRunLogsSubscriptionFailure";
  message: Scalars["String"]["output"];
  missingRunId?: Maybe<Scalars["String"]["output"]>;
};

export type PipelineRunLogsSubscriptionPayload =
  | PipelineRunLogsSubscriptionFailure
  | PipelineRunLogsSubscriptionSuccess;

export type PipelineRunLogsSubscriptionSuccess = {
  __typename?: "PipelineRunLogsSubscriptionSuccess";
  cursor: Scalars["String"]["output"];
  hasMorePastEvents: Scalars["Boolean"]["output"];
  messages: Array<DagsterRunEvent>;
  run: Run;
};

export type PipelineRunMetadataEntry = MetadataEntry & {
  __typename?: "PipelineRunMetadataEntry";
  description?: Maybe<Scalars["String"]["output"]>;
  label: Scalars["String"]["output"];
  runId: Scalars["String"]["output"];
};

export type PipelineRunNotFoundError = {
  message: Scalars["String"]["output"];
  runId: Scalars["String"]["output"];
};

export type PipelineRunStatsSnapshot = {
  endTime?: Maybe<Scalars["Float"]["output"]>;
  enqueuedTime?: Maybe<Scalars["Float"]["output"]>;
  expectations: Scalars["Int"]["output"];
  id: Scalars["String"]["output"];
  launchTime?: Maybe<Scalars["Float"]["output"]>;
  materializations: Scalars["Int"]["output"];
  runId: Scalars["String"]["output"];
  startTime?: Maybe<Scalars["Float"]["output"]>;
  stepsFailed: Scalars["Int"]["output"];
  stepsSucceeded: Scalars["Int"]["output"];
};

export type PipelineRunStepStats = {
  endTime?: Maybe<Scalars["Float"]["output"]>;
  expectationResults: Array<ExpectationResult>;
  materializations: Array<MaterializationEvent>;
  runId: Scalars["String"]["output"];
  startTime?: Maybe<Scalars["Float"]["output"]>;
  status?: Maybe<StepEventStatus>;
  stepKey: Scalars["String"]["output"];
};

export type PipelineRuns = {
  count?: Maybe<Scalars["Int"]["output"]>;
  results: Array<Run>;
};

/**
 * This type represents the fields necessary to identify a
 *         pipeline or pipeline subset.
 */
export type PipelineSelector = {
  assetCheckSelection?: InputMaybe<Array<AssetCheckHandleInput>>;
  assetSelection?: InputMaybe<Array<AssetKeyInput>>;
  pipelineName: Scalars["String"]["input"];
  repositoryLocationName: Scalars["String"]["input"];
  repositoryName: Scalars["String"]["input"];
  solidSelection?: InputMaybe<Array<Scalars["String"]["input"]>>;
};

export type PipelineSnapshot = IPipelineSnapshot &
  PipelineReference &
  SolidContainer & {
    __typename?: "PipelineSnapshot";
    dagsterTypeOrError: DagsterTypeOrError;
    dagsterTypes: Array<DagsterType>;
    description?: Maybe<Scalars["String"]["output"]>;
    graphName: Scalars["String"]["output"];
    id: Scalars["ID"]["output"];
    metadataEntries: Array<MetadataEntry>;
    modes: Array<Mode>;
    name: Scalars["String"]["output"];
    parentSnapshotId?: Maybe<Scalars["String"]["output"]>;
    pipelineSnapshotId: Scalars["String"]["output"];
    runTags: Array<PipelineTag>;
    runs: Array<Run>;
    schedules: Array<Schedule>;
    sensors: Array<Sensor>;
    solidHandle?: Maybe<SolidHandle>;
    solidHandles: Array<SolidHandle>;
    solidSelection?: Maybe<Array<Scalars["String"]["output"]>>;
    solids: Array<Solid>;
    tags: Array<PipelineTag>;
  };

export type PipelineSnapshotDagsterTypeOrErrorArgs = {
  dagsterTypeName: Scalars["String"]["input"];
};

export type PipelineSnapshotRunsArgs = {
  cursor?: InputMaybe<Scalars["String"]["input"]>;
  limit?: InputMaybe<Scalars["Int"]["input"]>;
};

export type PipelineSnapshotSolidHandleArgs = {
  handleID: Scalars["String"]["input"];
};

export type PipelineSnapshotSolidHandlesArgs = {
  parentHandleID?: InputMaybe<Scalars["String"]["input"]>;
};

export type PipelineSnapshotNotFoundError = Error & {
  __typename?: "PipelineSnapshotNotFoundError";
  message: Scalars["String"]["output"];
  snapshotId: Scalars["String"]["output"];
};

export type PipelineSnapshotOrError =
  | PipelineNotFoundError
  | PipelineSnapshot
  | PipelineSnapshotNotFoundError
  | PythonError;

export type PipelineTag = {
  __typename?: "PipelineTag";
  key: Scalars["String"]["output"];
  value: Scalars["String"]["output"];
};

/**
 * A run tag and the free-form values that have been associated
 *         with it so far.
 */
export type PipelineTagAndValues = {
  __typename?: "PipelineTagAndValues";
  key: Scalars["String"]["output"];
  values: Array<Scalars["String"]["output"]>;
};

export type PoolConfig = {
  __typename?: "PoolConfig";
  defaultPoolLimit?: Maybe<Scalars["Int"]["output"]>;
  opGranularityRunBuffer?: Maybe<Scalars["Int"]["output"]>;
  poolGranularity?: Maybe<Scalars["String"]["output"]>;
};

export type PoolMetadataEntry = MetadataEntry & {
  __typename?: "PoolMetadataEntry";
  description?: Maybe<Scalars["String"]["output"]>;
  label: Scalars["String"]["output"];
  pool: Scalars["String"]["output"];
};

export type PresetNotFoundError = Error & {
  __typename?: "PresetNotFoundError";
  message: Scalars["String"]["output"];
  preset: Scalars["String"]["output"];
};

export type PythonArtifactMetadataEntry = MetadataEntry & {
  __typename?: "PythonArtifactMetadataEntry";
  description?: Maybe<Scalars["String"]["output"]>;
  label: Scalars["String"]["output"];
  module: Scalars["String"]["output"];
  name: Scalars["String"]["output"];
};

export type PythonError = Error & {
  __typename?: "PythonError";
  cause?: Maybe<PythonError>;
  causes: Array<PythonError>;
  className?: Maybe<Scalars["String"]["output"]>;
  errorChain: Array<ErrorChainLink>;
  message: Scalars["String"]["output"];
  stack: Array<Scalars["String"]["output"]>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type Query = {
  __typename?: "Query";
  _service: _Service;
  /** Retrieve all the top level resources. */
  allTopLevelResourceDetailsOrError: ResourceDetailsListOrError;
  /** Fetch the partitions that would be targeted by a backfill, given the root partitions targeted. */
  assetBackfillPreview: Array<AssetPartitions>;
  /** Retrieve the executions for a given asset check. */
  assetCheckExecutions: Array<AssetCheckExecution>;
  /** Retrieve the condition evaluation for an asset and partition. */
  assetConditionEvaluationForPartition?: Maybe<AssetConditionEvaluation>;
  /** Retrieve the condition evaluation records for an asset. */
  assetConditionEvaluationRecordsOrError?: Maybe<AssetConditionEvaluationRecordsOrError>;
  /** Retrieve the condition evaluation records for a given evaluation ID. */
  assetConditionEvaluationsForEvaluationId?: Maybe<AssetConditionEvaluationRecordsOrError>;
  /** Retrieve a list of additional asset keys that must be materialized with the provided selection (due to @multi_assets with can_subset=False constraints.) */
  assetNodeAdditionalRequiredKeys: Array<AssetKey>;
  /** Retrieve a list of asset keys where two or more repos provide an asset definition. Note: Assets should not be defined in more than one repository - this query is used to present warnings and errors in the Dagster UI. */
  assetNodeDefinitionCollisions: Array<AssetNodeDefinitionCollision>;
  /** Retrieve an asset node by asset key. */
  assetNodeOrError: AssetNodeOrError;
  /** Retrieve asset nodes after applying a filter on asset group, job, and asset keys. */
  assetNodes: Array<AssetNode>;
  /** Retrieve an asset by asset key. */
  assetOrError: AssetOrError;
  /** Retrieve the latest materializations for a set of assets by asset keys. */
  assetsLatestInfo: Array<AssetLatestInfo>;
  /** Retrieve assets after applying a prefix filter, cursor, and limit. */
  assetsOrError: AssetsOrError;
  /** Retrieve the auto materialization evaluation records for an asset. */
  autoMaterializeAssetEvaluationsOrError?: Maybe<AutoMaterializeAssetEvaluationRecordsOrError>;
  /** Retrieve the auto materialization evaluation records for a given evaluation ID. */
  autoMaterializeEvaluationsForEvaluationId?: Maybe<AutoMaterializeAssetEvaluationRecordsOrError>;
  /** Fetch the history of auto-materialization ticks */
  autoMaterializeTicks: Array<InstigationTick>;
  /** Returns whether the user has permission to terminate runs in the deployment */
  canBulkTerminate: Scalars["Boolean"]["output"];
  /** Captured logs are the stdout/stderr logs for a given log key */
  capturedLogs: CapturedLogs;
  /** Retrieve the captured log metadata for a given log key. */
  capturedLogsMetadata: CapturedLogsMetadata;
  /** Retrieve the execution plan for a job and its run configuration. */
  executionPlanOrError: ExecutionPlanOrError;
  /** Retrieve a graph by its location name, repository name, and graph name. */
  graphOrError: GraphOrError;
  /** Retrieve the instance configuration for the Dagster deployment. */
  instance: Instance;
  /** Retrieve the state for a schedule or sensor by its location name, repository name, and schedule/sensor name. */
  instigationStateOrError: InstigationStateOrError;
  /** Retrieve the state for a group of instigators (schedule/sensor) by their containing repository id. */
  instigationStatesOrError: InstigationStatesOrError;
  /** Retrieve whether the run configuration is valid or invalid. */
  isPipelineConfigValid: PipelineConfigValidationResult;
  /** Retrieve location status for workspace locations. */
  locationStatusesOrError: WorkspaceLocationStatusEntriesOrError;
  /** Retrieve event logs after applying a run id filter, cursor, and limit. */
  logsForRun: EventConnectionOrError;
  oso_artifactsByCollectionV1?: Maybe<Array<Oso_ArtifactsByCollectionV1>>;
  oso_artifactsByProjectV1?: Maybe<Array<Oso_ArtifactsByProjectV1>>;
  oso_artifactsByUserV1?: Maybe<Array<Oso_ArtifactsByUserV1>>;
  oso_artifactsV1?: Maybe<Array<Oso_ArtifactsV1>>;
  oso_codeMetricsByArtifactV0?: Maybe<Array<Oso_CodeMetricsByArtifactV0>>;
  oso_codeMetricsByProjectV1?: Maybe<Array<Oso_CodeMetricsByProjectV1>>;
  oso_collectionsV1?: Maybe<Array<Oso_CollectionsV1>>;
  oso_contractsV0?: Maybe<Array<Oso_ContractsV0>>;
  oso_contractsV0ByDeploymentDate?: Maybe<Oso_ContractsV0>;
  oso_eventTypesV1?: Maybe<Array<Oso_EventTypesV1>>;
  oso_fundingMetricsByProjectV1?: Maybe<Array<Oso_FundingMetricsByProjectV1>>;
  oso_keyMetricsByArtifactV0?: Maybe<Array<Oso_KeyMetricsByArtifactV0>>;
  oso_keyMetricsByCollectionV0?: Maybe<Array<Oso_KeyMetricsByCollectionV0>>;
  oso_keyMetricsByProjectV0?: Maybe<Array<Oso_KeyMetricsByProjectV0>>;
  oso_metricsV0?: Maybe<Array<Oso_MetricsV0>>;
  oso_metricsV0ByMetricSourceMetricNamespaceMetricName?: Maybe<Oso_MetricsV0>;
  oso_modelsV0?: Maybe<Array<Oso_ModelsV0>>;
  oso_onchainMetricsByProjectV1?: Maybe<Array<Oso_OnchainMetricsByProjectV1>>;
  oso_packageOwnersV0?: Maybe<Array<Oso_PackageOwnersV0>>;
  oso_projectsByCollectionV1?: Maybe<Array<Oso_ProjectsByCollectionV1>>;
  oso_projectsV1?: Maybe<Array<Oso_ProjectsV1>>;
  oso_repositoriesV0?: Maybe<Array<Oso_RepositoriesV0>>;
  oso_sbomsV0?: Maybe<Array<Oso_SbomsV0>>;
  oso_timeseriesEventsByArtifactV0?: Maybe<
    Array<Oso_TimeseriesEventsByArtifactV0>
  >;
  oso_timeseriesMetricsByArtifactV0?: Maybe<
    Array<Oso_TimeseriesMetricsByArtifactV0>
  >;
  oso_timeseriesMetricsByArtifactV0ByMetricIdArtifactIdSampleDate?: Maybe<Oso_TimeseriesMetricsByArtifactV0>;
  oso_timeseriesMetricsByCollectionV0?: Maybe<
    Array<Oso_TimeseriesMetricsByCollectionV0>
  >;
  oso_timeseriesMetricsByCollectionV0ByMetricIdCollectionIdSampleDate?: Maybe<Oso_TimeseriesMetricsByCollectionV0>;
  oso_timeseriesMetricsByProjectV0?: Maybe<
    Array<Oso_TimeseriesMetricsByProjectV0>
  >;
  oso_timeseriesMetricsByProjectV0ByMetricIdProjectIdSampleDate?: Maybe<Oso_TimeseriesMetricsByProjectV0>;
  oso_usersV1?: Maybe<Array<Oso_UsersV1>>;
  /** Retrieve a backfill by backfill id. */
  partitionBackfillOrError: PartitionBackfillOrError;
  /** Retrieve backfills after applying a status filter, cursor, and limit. */
  partitionBackfillsOrError: PartitionBackfillsOrError;
  /** Retrieve a partition set by its location name, repository name, and partition set name. */
  partitionSetOrError: PartitionSetOrError;
  /** Retrieve the partition sets for a job by its location name, repository name, and job name. */
  partitionSetsOrError: PartitionSetsOrError;
  /** Retrieve the set of permissions for the Dagster deployment. */
  permissions: Array<Permission>;
  /** Retrieve a job by its location name, repository name, and job name. */
  pipelineOrError: PipelineOrError;
  /** Retrieve a run by its run id. */
  pipelineRunOrError: RunOrError;
  /** Retrieve runs after applying a filter, cursor, and limit. */
  pipelineRunsOrError: RunsOrError;
  /** Retrieve a job snapshot by its id or location name, repository name, and job name. */
  pipelineSnapshotOrError: PipelineSnapshotOrError;
  /** Retrieve all the repositories. */
  repositoriesOrError: RepositoriesOrError;
  /** Retrieve a repository by its location name and repository name. */
  repositoryOrError: RepositoryOrError;
  /** Retrieve the list of resources for a given job. */
  resourcesOrError: ResourcesOrError;
  /** Retrieve the run configuration schema for a job. */
  runConfigSchemaOrError: RunConfigSchemaOrError;
  /** Retrieve a group of runs with the matching root run id. */
  runGroupOrError: RunGroupOrError;
  /** Retrieve run IDs after applying a filter, cursor, and limit. */
  runIdsOrError: RunIdsOrError;
  /** Retrieve a run by its run id. */
  runOrError: RunOrError;
  /** Retrieve the distinct tag keys from all runs. */
  runTagKeysOrError?: Maybe<RunTagKeysOrError>;
  /** Retrieve all the distinct key-value tags from all runs. */
  runTagsOrError?: Maybe<RunTagsOrError>;
  /** Retrieve the number of entries for the Runs Feed after applying a filter. */
  runsFeedCountOrError: RunsFeedCountOrError;
  /** Retrieve entries for the Runs Feed after applying a filter, cursor and limit. */
  runsFeedOrError: RunsFeedConnectionOrError;
  /** Retrieve runs after applying a filter, cursor, and limit. */
  runsOrError: RunsOrError;
  /** Retrieve a schedule by its location name, repository name, and schedule name. */
  scheduleOrError: ScheduleOrError;
  /** Retrieve the name of the scheduler running in the Dagster deployment. */
  scheduler: SchedulerOrError;
  /** Retrieve all the schedules. */
  schedulesOrError: SchedulesOrError;
  /** Retrieve a sensor by its location name, repository name, and sensor name. */
  sensorOrError: SensorOrError;
  /** Retrieve all the sensors. */
  sensorsOrError: SensorsOrError;
  /** Whether or not the NUX should be shown to the user */
  shouldShowNux: Scalars["Boolean"]["output"];
  /** Provides fields for testing behavior */
  test?: Maybe<TestFields>;
  /** Retrieve a top level resource by its location name, repository name, and resource name. */
  topLevelResourceDetailsOrError: ResourceDetailsOrError;
  /** Retrieve the partition keys which were true for a specific automation condition evaluation node. */
  truePartitionsForAutomationConditionEvaluationNode: Array<
    Scalars["String"]["output"]
  >;
  /** Retrieve all the utilized environment variables for the given repo. */
  utilizedEnvVarsOrError: EnvVarWithConsumersOrError;
  /** Retrieve the version of Dagster running in the Dagster deployment. */
  version: Scalars["String"]["output"];
  /** Retrieve a workspace entry by name. */
  workspaceLocationEntryOrError?: Maybe<WorkspaceLocationEntryOrError>;
  /** Retrieve the workspace and its locations. */
  workspaceOrError: WorkspaceOrError;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryAllTopLevelResourceDetailsOrErrorArgs = {
  repositorySelector: RepositorySelector;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryAssetBackfillPreviewArgs = {
  params: AssetBackfillPreviewParams;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryAssetCheckExecutionsArgs = {
  assetKey: AssetKeyInput;
  checkName: Scalars["String"]["input"];
  cursor?: InputMaybe<Scalars["String"]["input"]>;
  limit: Scalars["Int"]["input"];
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryAssetConditionEvaluationForPartitionArgs = {
  assetKey?: InputMaybe<AssetKeyInput>;
  evaluationId: Scalars["ID"]["input"];
  partition: Scalars["String"]["input"];
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryAssetConditionEvaluationRecordsOrErrorArgs = {
  assetCheckKey?: InputMaybe<AssetCheckHandleInput>;
  assetKey?: InputMaybe<AssetKeyInput>;
  cursor?: InputMaybe<Scalars["String"]["input"]>;
  limit: Scalars["Int"]["input"];
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryAssetConditionEvaluationsForEvaluationIdArgs = {
  evaluationId: Scalars["ID"]["input"];
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryAssetNodeAdditionalRequiredKeysArgs = {
  assetKeys: Array<AssetKeyInput>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryAssetNodeDefinitionCollisionsArgs = {
  assetKeys: Array<AssetKeyInput>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryAssetNodeOrErrorArgs = {
  assetKey: AssetKeyInput;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryAssetNodesArgs = {
  assetKeys?: InputMaybe<Array<AssetKeyInput>>;
  group?: InputMaybe<AssetGroupSelector>;
  loadMaterializations?: InputMaybe<Scalars["Boolean"]["input"]>;
  pipeline?: InputMaybe<PipelineSelector>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryAssetOrErrorArgs = {
  assetKey: AssetKeyInput;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryAssetsLatestInfoArgs = {
  assetKeys: Array<AssetKeyInput>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryAssetsOrErrorArgs = {
  cursor?: InputMaybe<Scalars["String"]["input"]>;
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  prefix?: InputMaybe<Array<Scalars["String"]["input"]>>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryAutoMaterializeAssetEvaluationsOrErrorArgs = {
  assetKey: AssetKeyInput;
  cursor?: InputMaybe<Scalars["String"]["input"]>;
  limit: Scalars["Int"]["input"];
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryAutoMaterializeEvaluationsForEvaluationIdArgs = {
  evaluationId: Scalars["ID"]["input"];
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryAutoMaterializeTicksArgs = {
  afterTimestamp?: InputMaybe<Scalars["Float"]["input"]>;
  beforeTimestamp?: InputMaybe<Scalars["Float"]["input"]>;
  cursor?: InputMaybe<Scalars["String"]["input"]>;
  dayOffset?: InputMaybe<Scalars["Int"]["input"]>;
  dayRange?: InputMaybe<Scalars["Int"]["input"]>;
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  statuses?: InputMaybe<Array<InstigationTickStatus>>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryCapturedLogsArgs = {
  cursor?: InputMaybe<Scalars["String"]["input"]>;
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  logKey: Array<Scalars["String"]["input"]>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryCapturedLogsMetadataArgs = {
  logKey: Array<Scalars["String"]["input"]>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryExecutionPlanOrErrorArgs = {
  mode: Scalars["String"]["input"];
  pipeline: PipelineSelector;
  runConfigData?: InputMaybe<Scalars["RunConfigData"]["input"]>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryGraphOrErrorArgs = {
  selector?: InputMaybe<GraphSelector>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryInstigationStateOrErrorArgs = {
  id?: InputMaybe<Scalars["String"]["input"]>;
  instigationSelector: InstigationSelector;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryInstigationStatesOrErrorArgs = {
  repositoryID: Scalars["String"]["input"];
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryIsPipelineConfigValidArgs = {
  mode: Scalars["String"]["input"];
  pipeline: PipelineSelector;
  runConfigData?: InputMaybe<Scalars["RunConfigData"]["input"]>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryLogsForRunArgs = {
  afterCursor?: InputMaybe<Scalars["String"]["input"]>;
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  runId: Scalars["ID"]["input"];
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryOso_ArtifactsByCollectionV1Args = {
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  offset?: InputMaybe<Scalars["Int"]["input"]>;
  order_by?: InputMaybe<Array<Oso_ArtifactsByCollectionV1OrderByExp>>;
  where?: InputMaybe<Oso_ArtifactsByCollectionV1BoolExp>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryOso_ArtifactsByProjectV1Args = {
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  offset?: InputMaybe<Scalars["Int"]["input"]>;
  order_by?: InputMaybe<Array<Oso_ArtifactsByProjectV1OrderBy>>;
  where?: InputMaybe<Oso_ArtifactsByProjectV1BoolExp>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryOso_ArtifactsByUserV1Args = {
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  offset?: InputMaybe<Scalars["Int"]["input"]>;
  order_by?: InputMaybe<Array<Oso_ArtifactsByUserV1OrderByExp>>;
  where?: InputMaybe<Oso_ArtifactsByUserV1BoolExp>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryOso_ArtifactsV1Args = {
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  offset?: InputMaybe<Scalars["Int"]["input"]>;
  order_by?: InputMaybe<Array<Oso_ArtifactsV1OrderByExp>>;
  where?: InputMaybe<Oso_ArtifactsV1BoolExp>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryOso_CodeMetricsByArtifactV0Args = {
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  offset?: InputMaybe<Scalars["Int"]["input"]>;
  order_by?: InputMaybe<Array<Oso_CodeMetricsByArtifactV0OrderBy>>;
  where?: InputMaybe<Oso_CodeMetricsByArtifactV0BoolExp>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryOso_CodeMetricsByProjectV1Args = {
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  offset?: InputMaybe<Scalars["Int"]["input"]>;
  order_by?: InputMaybe<Array<Oso_CodeMetricsByProjectV1OrderBy>>;
  where?: InputMaybe<Oso_CodeMetricsByProjectV1BoolExp>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryOso_CollectionsV1Args = {
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  offset?: InputMaybe<Scalars["Int"]["input"]>;
  order_by?: InputMaybe<Array<Oso_CollectionsV1OrderBy>>;
  where?: InputMaybe<Oso_CollectionsV1BoolExp>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryOso_ContractsV0Args = {
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  offset?: InputMaybe<Scalars["Int"]["input"]>;
  order_by?: InputMaybe<Array<Oso_ContractsV0OrderByExp>>;
  where?: InputMaybe<Oso_ContractsV0BoolExp>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryOso_ContractsV0ByDeploymentDateArgs = {
  deploymentDate: Scalars["Oso_Date"]["input"];
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryOso_EventTypesV1Args = {
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  offset?: InputMaybe<Scalars["Int"]["input"]>;
  order_by?: InputMaybe<Array<Oso_EventTypesV1OrderBy>>;
  where?: InputMaybe<Oso_EventTypesV1BoolExp>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryOso_FundingMetricsByProjectV1Args = {
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  offset?: InputMaybe<Scalars["Int"]["input"]>;
  order_by?: InputMaybe<Array<Oso_FundingMetricsByProjectV1OrderBy>>;
  where?: InputMaybe<Oso_FundingMetricsByProjectV1BoolExp>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryOso_KeyMetricsByArtifactV0Args = {
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  offset?: InputMaybe<Scalars["Int"]["input"]>;
  order_by?: InputMaybe<Array<Oso_KeyMetricsByArtifactV0OrderByExp>>;
  where?: InputMaybe<Oso_KeyMetricsByArtifactV0BoolExp>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryOso_KeyMetricsByCollectionV0Args = {
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  offset?: InputMaybe<Scalars["Int"]["input"]>;
  order_by?: InputMaybe<Array<Oso_KeyMetricsByCollectionV0OrderByExp>>;
  where?: InputMaybe<Oso_KeyMetricsByCollectionV0BoolExp>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryOso_KeyMetricsByProjectV0Args = {
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  offset?: InputMaybe<Scalars["Int"]["input"]>;
  order_by?: InputMaybe<Array<Oso_KeyMetricsByProjectV0OrderByExp>>;
  where?: InputMaybe<Oso_KeyMetricsByProjectV0BoolExp>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryOso_MetricsV0Args = {
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  offset?: InputMaybe<Scalars["Int"]["input"]>;
  order_by?: InputMaybe<Array<Oso_MetricsV0OrderBy>>;
  where?: InputMaybe<Oso_MetricsV0BoolExp>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryOso_MetricsV0ByMetricSourceMetricNamespaceMetricNameArgs = {
  metricName: Scalars["String"]["input"];
  metricNamespace: Scalars["String"]["input"];
  metricSource: Scalars["String"]["input"];
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryOso_ModelsV0Args = {
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  offset?: InputMaybe<Scalars["Int"]["input"]>;
  order_by?: InputMaybe<Array<Oso_ModelsV0OrderByExp>>;
  where?: InputMaybe<Oso_ModelsV0BoolExp>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryOso_OnchainMetricsByProjectV1Args = {
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  offset?: InputMaybe<Scalars["Int"]["input"]>;
  order_by?: InputMaybe<Array<Oso_OnchainMetricsByProjectV1OrderBy>>;
  where?: InputMaybe<Oso_OnchainMetricsByProjectV1BoolExp>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryOso_PackageOwnersV0Args = {
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  offset?: InputMaybe<Scalars["Int"]["input"]>;
  order_by?: InputMaybe<Array<Oso_PackageOwnersV0OrderByExp>>;
  where?: InputMaybe<Oso_PackageOwnersV0BoolExp>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryOso_ProjectsByCollectionV1Args = {
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  offset?: InputMaybe<Scalars["Int"]["input"]>;
  order_by?: InputMaybe<Array<Oso_ProjectsByCollectionV1OrderBy>>;
  where?: InputMaybe<Oso_ProjectsByCollectionV1BoolExp>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryOso_ProjectsV1Args = {
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  offset?: InputMaybe<Scalars["Int"]["input"]>;
  order_by?: InputMaybe<Array<Oso_ProjectsV1OrderBy>>;
  where?: InputMaybe<Oso_ProjectsV1BoolExp>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryOso_RepositoriesV0Args = {
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  offset?: InputMaybe<Scalars["Int"]["input"]>;
  order_by?: InputMaybe<Array<Oso_RepositoriesV0OrderByExp>>;
  where?: InputMaybe<Oso_RepositoriesV0BoolExp>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryOso_SbomsV0Args = {
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  offset?: InputMaybe<Scalars["Int"]["input"]>;
  order_by?: InputMaybe<Array<Oso_SbomsV0OrderByExp>>;
  where?: InputMaybe<Oso_SbomsV0BoolExp>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryOso_TimeseriesEventsByArtifactV0Args = {
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  offset?: InputMaybe<Scalars["Int"]["input"]>;
  order_by?: InputMaybe<Array<Oso_TimeseriesEventsByArtifactV0OrderBy>>;
  where?: InputMaybe<Oso_TimeseriesEventsByArtifactV0BoolExp>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryOso_TimeseriesMetricsByArtifactV0Args = {
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  offset?: InputMaybe<Scalars["Int"]["input"]>;
  order_by?: InputMaybe<Array<Oso_TimeseriesMetricsByArtifactV0OrderBy>>;
  where?: InputMaybe<Oso_TimeseriesMetricsByArtifactV0BoolExp>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryOso_TimeseriesMetricsByArtifactV0ByMetricIdArtifactIdSampleDateArgs =
  {
    artifactId: Scalars["String"]["input"];
    metricId: Scalars["String"]["input"];
    sampleDate: Scalars["Oso_Date"]["input"];
  };

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryOso_TimeseriesMetricsByCollectionV0Args = {
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  offset?: InputMaybe<Scalars["Int"]["input"]>;
  order_by?: InputMaybe<Array<Oso_TimeseriesMetricsByCollectionV0OrderBy>>;
  where?: InputMaybe<Oso_TimeseriesMetricsByCollectionV0BoolExp>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryOso_TimeseriesMetricsByCollectionV0ByMetricIdCollectionIdSampleDateArgs =
  {
    collectionId: Scalars["String"]["input"];
    metricId: Scalars["String"]["input"];
    sampleDate: Scalars["Oso_Date"]["input"];
  };

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryOso_TimeseriesMetricsByProjectV0Args = {
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  offset?: InputMaybe<Scalars["Int"]["input"]>;
  order_by?: InputMaybe<Array<Oso_TimeseriesMetricsByProjectV0OrderBy>>;
  where?: InputMaybe<Oso_TimeseriesMetricsByProjectV0BoolExp>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryOso_TimeseriesMetricsByProjectV0ByMetricIdProjectIdSampleDateArgs =
  {
    metricId: Scalars["String"]["input"];
    projectId: Scalars["String"]["input"];
    sampleDate: Scalars["Oso_Date"]["input"];
  };

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryOso_UsersV1Args = {
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  offset?: InputMaybe<Scalars["Int"]["input"]>;
  order_by?: InputMaybe<Array<Oso_UsersV1OrderBy>>;
  where?: InputMaybe<Oso_UsersV1BoolExp>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryPartitionBackfillOrErrorArgs = {
  backfillId: Scalars["String"]["input"];
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryPartitionBackfillsOrErrorArgs = {
  cursor?: InputMaybe<Scalars["String"]["input"]>;
  filters?: InputMaybe<BulkActionsFilter>;
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  status?: InputMaybe<BulkActionStatus>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryPartitionSetOrErrorArgs = {
  partitionSetName?: InputMaybe<Scalars["String"]["input"]>;
  repositorySelector: RepositorySelector;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryPartitionSetsOrErrorArgs = {
  pipelineName: Scalars["String"]["input"];
  repositorySelector: RepositorySelector;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryPipelineOrErrorArgs = {
  params: PipelineSelector;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryPipelineRunOrErrorArgs = {
  runId: Scalars["ID"]["input"];
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryPipelineRunsOrErrorArgs = {
  cursor?: InputMaybe<Scalars["String"]["input"]>;
  filter?: InputMaybe<RunsFilter>;
  limit?: InputMaybe<Scalars["Int"]["input"]>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryPipelineSnapshotOrErrorArgs = {
  activePipelineSelector?: InputMaybe<PipelineSelector>;
  snapshotId?: InputMaybe<Scalars["String"]["input"]>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryRepositoriesOrErrorArgs = {
  repositorySelector?: InputMaybe<RepositorySelector>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryRepositoryOrErrorArgs = {
  repositorySelector: RepositorySelector;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryResourcesOrErrorArgs = {
  pipelineSelector: PipelineSelector;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryRunConfigSchemaOrErrorArgs = {
  mode?: InputMaybe<Scalars["String"]["input"]>;
  selector: PipelineSelector;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryRunGroupOrErrorArgs = {
  runId: Scalars["ID"]["input"];
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryRunIdsOrErrorArgs = {
  cursor?: InputMaybe<Scalars["String"]["input"]>;
  filter?: InputMaybe<RunsFilter>;
  limit?: InputMaybe<Scalars["Int"]["input"]>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryRunOrErrorArgs = {
  runId: Scalars["ID"]["input"];
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryRunTagsOrErrorArgs = {
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  tagKeys?: InputMaybe<Array<Scalars["String"]["input"]>>;
  valuePrefix?: InputMaybe<Scalars["String"]["input"]>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryRunsFeedCountOrErrorArgs = {
  filter?: InputMaybe<RunsFilter>;
  view: RunsFeedView;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryRunsFeedOrErrorArgs = {
  cursor?: InputMaybe<Scalars["String"]["input"]>;
  filter?: InputMaybe<RunsFilter>;
  limit: Scalars["Int"]["input"];
  view: RunsFeedView;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryRunsOrErrorArgs = {
  cursor?: InputMaybe<Scalars["String"]["input"]>;
  filter?: InputMaybe<RunsFilter>;
  limit?: InputMaybe<Scalars["Int"]["input"]>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryScheduleOrErrorArgs = {
  scheduleSelector: ScheduleSelector;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QuerySchedulesOrErrorArgs = {
  repositorySelector: RepositorySelector;
  scheduleStatus?: InputMaybe<InstigationStatus>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QuerySensorOrErrorArgs = {
  sensorSelector: SensorSelector;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QuerySensorsOrErrorArgs = {
  repositorySelector: RepositorySelector;
  sensorStatus?: InputMaybe<InstigationStatus>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryTopLevelResourceDetailsOrErrorArgs = {
  resourceSelector: ResourceSelector;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryTruePartitionsForAutomationConditionEvaluationNodeArgs = {
  assetKey?: InputMaybe<AssetKeyInput>;
  evaluationId: Scalars["ID"]["input"];
  nodeUniqueId?: InputMaybe<Scalars["String"]["input"]>;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryUtilizedEnvVarsOrErrorArgs = {
  repositorySelector: RepositorySelector;
};

/** The root for all queries to retrieve data from the Dagster instance. */
export type QueryWorkspaceLocationEntryOrErrorArgs = {
  name: Scalars["String"]["input"];
};

export type ReexecutionParams = {
  parentRunId: Scalars["String"]["input"];
  strategy: ReexecutionStrategy;
};

export enum ReexecutionStrategy {
  AllSteps = "ALL_STEPS",
  FromFailure = "FROM_FAILURE",
}

/** Regular is an odd name in this context. It really means Scalar or Any. */
export type RegularConfigType = ConfigType & {
  __typename?: "RegularConfigType";
  description?: Maybe<Scalars["String"]["output"]>;
  givenName: Scalars["String"]["output"];
  isSelector: Scalars["Boolean"]["output"];
  key: Scalars["String"]["output"];
  /**
   *
   * This is an odd and problematic field. It recursively goes down to
   * get all the types contained within a type. The case where it is horrible
   * are dictionaries and it recurses all the way down to the leaves. This means
   * that in a case where one is fetching all the types and then all the inner
   * types keys for those types, we are returning O(N^2) type keys, which
   * can cause awful performance for large schemas. When you have access
   * to *all* the types, you should instead only use the type_param_keys
   * field for closed generic types and manually navigate down the to
   * field types client-side.
   *
   * Where it is useful is when you are fetching types independently and
   * want to be able to render them, but without fetching the entire schema.
   *
   * We use this capability when rendering the sidebar.
   *
   */
  recursiveConfigTypes: Array<ConfigType>;
  /**
   *
   * This returns the keys for type parameters of any closed generic type,
   * (e.g. List, Optional). This should be used for reconstructing and
   * navigating the full schema client-side and not innerTypes.
   *
   */
  typeParamKeys: Array<Scalars["String"]["output"]>;
};

export type RegularDagsterType = DagsterType & {
  __typename?: "RegularDagsterType";
  description?: Maybe<Scalars["String"]["output"]>;
  displayName: Scalars["String"]["output"];
  innerTypes: Array<DagsterType>;
  inputSchemaType?: Maybe<ConfigType>;
  isBuiltin: Scalars["Boolean"]["output"];
  isList: Scalars["Boolean"]["output"];
  isNothing: Scalars["Boolean"]["output"];
  isNullable: Scalars["Boolean"]["output"];
  key: Scalars["String"]["output"];
  metadataEntries: Array<MetadataEntry>;
  name?: Maybe<Scalars["String"]["output"]>;
  outputSchemaType?: Maybe<ConfigType>;
};

export type ReloadNotSupported = Error & {
  __typename?: "ReloadNotSupported";
  message: Scalars["String"]["output"];
};

/** Reloads a code location server. */
export type ReloadRepositoryLocationMutation = {
  __typename?: "ReloadRepositoryLocationMutation";
  Output: ReloadRepositoryLocationMutationResult;
};

/** The output from reloading a code location server. */
export type ReloadRepositoryLocationMutationResult =
  | PythonError
  | ReloadNotSupported
  | RepositoryLocationNotFound
  | UnauthorizedError
  | WorkspaceLocationEntry;

/** Reloads the workspace and its code location servers. */
export type ReloadWorkspaceMutation = {
  __typename?: "ReloadWorkspaceMutation";
  Output: ReloadWorkspaceMutationResult;
};

/** The output from reloading the workspace. */
export type ReloadWorkspaceMutationResult =
  | PythonError
  | UnauthorizedError
  | Workspace;

export type ReportRunlessAssetEventsParams = {
  assetKey: AssetKeyInput;
  description?: InputMaybe<Scalars["String"]["input"]>;
  eventType: AssetEventType;
  partitionKeys?: InputMaybe<Array<InputMaybe<Scalars["String"]["input"]>>>;
};

/** The output from reporting runless events. */
export type ReportRunlessAssetEventsResult =
  | PythonError
  | ReportRunlessAssetEventsSuccess
  | UnauthorizedError;

/** Output indicating that runless asset events were reported. */
export type ReportRunlessAssetEventsSuccess = {
  __typename?: "ReportRunlessAssetEventsSuccess";
  assetKey: AssetKey;
};

export type RepositoriesOrError =
  | PythonError
  | RepositoryConnection
  | RepositoryNotFoundError;

export type Repository = {
  __typename?: "Repository";
  allTopLevelResourceDetails: Array<ResourceDetails>;
  assetGroups: Array<AssetGroup>;
  assetNodes: Array<AssetNode>;
  displayMetadata: Array<RepositoryMetadata>;
  id: Scalars["ID"]["output"];
  jobs: Array<Job>;
  location: RepositoryLocation;
  name: Scalars["String"]["output"];
  origin: RepositoryOrigin;
  partitionSets: Array<PartitionSet>;
  pipelines: Array<Pipeline>;
  schedules: Array<Schedule>;
  sensors: Array<Sensor>;
  usedSolid?: Maybe<UsedSolid>;
  usedSolids: Array<UsedSolid>;
};

export type RepositorySensorsArgs = {
  sensorType?: InputMaybe<SensorType>;
};

export type RepositoryUsedSolidArgs = {
  name: Scalars["String"]["input"];
};

export type RepositoryConnection = {
  __typename?: "RepositoryConnection";
  nodes: Array<Repository>;
};

export type RepositoryLocation = {
  __typename?: "RepositoryLocation";
  dagsterLibraryVersions?: Maybe<Array<DagsterLibraryVersion>>;
  environmentPath?: Maybe<Scalars["String"]["output"]>;
  id: Scalars["ID"]["output"];
  isReloadSupported: Scalars["Boolean"]["output"];
  name: Scalars["String"]["output"];
  repositories: Array<Repository>;
  serverId?: Maybe<Scalars["String"]["output"]>;
};

export enum RepositoryLocationLoadStatus {
  Loaded = "LOADED",
  Loading = "LOADING",
}

export type RepositoryLocationNotFound = Error & {
  __typename?: "RepositoryLocationNotFound";
  message: Scalars["String"]["output"];
};

export type RepositoryLocationOrLoadError = PythonError | RepositoryLocation;

export type RepositoryMetadata = {
  __typename?: "RepositoryMetadata";
  key: Scalars["String"]["output"];
  value: Scalars["String"]["output"];
};

export type RepositoryNotFoundError = Error & {
  __typename?: "RepositoryNotFoundError";
  message: Scalars["String"]["output"];
  repositoryLocationName: Scalars["String"]["output"];
  repositoryName: Scalars["String"]["output"];
};

export type RepositoryOrError =
  | PythonError
  | Repository
  | RepositoryNotFoundError;

export type RepositoryOrigin = {
  __typename?: "RepositoryOrigin";
  id: Scalars["String"]["output"];
  repositoryLocationMetadata: Array<RepositoryMetadata>;
  repositoryLocationName: Scalars["String"]["output"];
  repositoryName: Scalars["String"]["output"];
};

/** This type represents the fields necessary to identify a repository. */
export type RepositorySelector = {
  repositoryLocationName: Scalars["String"]["input"];
  repositoryName: Scalars["String"]["input"];
};

export type RequestedMaterializationsForAsset = {
  __typename?: "RequestedMaterializationsForAsset";
  assetKey: AssetKey;
  partitionKeys: Array<Scalars["String"]["output"]>;
};

/** Reset a schedule to its status defined in code, otherwise disable it from launching runs for a job. */
export type ResetScheduleMutation = {
  __typename?: "ResetScheduleMutation";
  Output: ScheduleMutationResult;
};

/** Reset a sensor to its status defined in code, otherwise disable it from launching runs for a job. */
export type ResetSensorMutation = {
  __typename?: "ResetSensorMutation";
  Output: SensorOrError;
};

export type Resource = {
  __typename?: "Resource";
  configField?: Maybe<ConfigTypeField>;
  description?: Maybe<Scalars["String"]["output"]>;
  name: Scalars["String"]["output"];
};

export type ResourceConnection = {
  __typename?: "ResourceConnection";
  resources: Array<Resource>;
};

export type ResourceDetails = {
  __typename?: "ResourceDetails";
  assetKeysUsing: Array<AssetKey>;
  /** Snapshots of all the fields for the given resource */
  configFields: Array<ConfigTypeField>;
  /** List of K/V pairs of user-configured values for each of the top-level fields on the resource */
  configuredValues: Array<ConfiguredValue>;
  description?: Maybe<Scalars["String"]["output"]>;
  id: Scalars["String"]["output"];
  isTopLevel: Scalars["Boolean"]["output"];
  jobsOpsUsing: Array<JobWithOps>;
  name: Scalars["String"]["output"];
  /** List of nested resources for the given resource */
  nestedResources: Array<NestedResourceEntry>;
  /** List of parent resources for the given resource */
  parentResources: Array<NestedResourceEntry>;
  resourceType: Scalars["String"]["output"];
  schedulesUsing: Array<Scalars["String"]["output"]>;
  sensorsUsing: Array<Scalars["String"]["output"]>;
};

export type ResourceDetailsList = {
  __typename?: "ResourceDetailsList";
  results: Array<ResourceDetails>;
};

export type ResourceDetailsListOrError =
  | PythonError
  | RepositoryNotFoundError
  | ResourceDetailsList;

export type ResourceDetailsOrError =
  | PythonError
  | ResourceDetails
  | ResourceNotFoundError;

export type ResourceInitFailureEvent = DisplayableEvent &
  ErrorEvent &
  MarkerEvent &
  MessageEvent &
  StepEvent & {
    __typename?: "ResourceInitFailureEvent";
    description?: Maybe<Scalars["String"]["output"]>;
    error?: Maybe<PythonError>;
    eventType?: Maybe<DagsterEventType>;
    label?: Maybe<Scalars["String"]["output"]>;
    level: LogLevel;
    markerEnd?: Maybe<Scalars["String"]["output"]>;
    markerStart?: Maybe<Scalars["String"]["output"]>;
    message: Scalars["String"]["output"];
    metadataEntries: Array<MetadataEntry>;
    runId: Scalars["String"]["output"];
    solidHandleID?: Maybe<Scalars["String"]["output"]>;
    stepKey?: Maybe<Scalars["String"]["output"]>;
    timestamp: Scalars["String"]["output"];
  };

export type ResourceInitStartedEvent = DisplayableEvent &
  MarkerEvent &
  MessageEvent &
  StepEvent & {
    __typename?: "ResourceInitStartedEvent";
    description?: Maybe<Scalars["String"]["output"]>;
    eventType?: Maybe<DagsterEventType>;
    label?: Maybe<Scalars["String"]["output"]>;
    level: LogLevel;
    markerEnd?: Maybe<Scalars["String"]["output"]>;
    markerStart?: Maybe<Scalars["String"]["output"]>;
    message: Scalars["String"]["output"];
    metadataEntries: Array<MetadataEntry>;
    runId: Scalars["String"]["output"];
    solidHandleID?: Maybe<Scalars["String"]["output"]>;
    stepKey?: Maybe<Scalars["String"]["output"]>;
    timestamp: Scalars["String"]["output"];
  };

export type ResourceInitSuccessEvent = DisplayableEvent &
  MarkerEvent &
  MessageEvent &
  StepEvent & {
    __typename?: "ResourceInitSuccessEvent";
    description?: Maybe<Scalars["String"]["output"]>;
    eventType?: Maybe<DagsterEventType>;
    label?: Maybe<Scalars["String"]["output"]>;
    level: LogLevel;
    markerEnd?: Maybe<Scalars["String"]["output"]>;
    markerStart?: Maybe<Scalars["String"]["output"]>;
    message: Scalars["String"]["output"];
    metadataEntries: Array<MetadataEntry>;
    runId: Scalars["String"]["output"];
    solidHandleID?: Maybe<Scalars["String"]["output"]>;
    stepKey?: Maybe<Scalars["String"]["output"]>;
    timestamp: Scalars["String"]["output"];
  };

export type ResourceNotFoundError = Error & {
  __typename?: "ResourceNotFoundError";
  message: Scalars["String"]["output"];
  resourceName: Scalars["String"]["output"];
};

export type ResourceRequirement = {
  __typename?: "ResourceRequirement";
  resourceKey: Scalars["String"]["output"];
};

/** This type represents the fields necessary to identify a top-level resource. */
export type ResourceSelector = {
  repositoryLocationName: Scalars["String"]["input"];
  repositoryName: Scalars["String"]["input"];
  resourceName: Scalars["String"]["input"];
};

export type ResourcesOrError =
  | InvalidSubsetError
  | PipelineNotFoundError
  | PythonError
  | ResourceConnection;

export type ResumeBackfillResult =
  | PythonError
  | ResumeBackfillSuccess
  | UnauthorizedError;

export type ResumeBackfillSuccess = {
  __typename?: "ResumeBackfillSuccess";
  backfillId: Scalars["String"]["output"];
};

export type Run = PipelineRun &
  RunsFeedEntry & {
    __typename?: "Run";
    allPools?: Maybe<Array<Scalars["String"]["output"]>>;
    assetCheckSelection?: Maybe<Array<AssetCheckhandle>>;
    assetChecks?: Maybe<Array<AssetCheckhandle>>;
    assetMaterializations: Array<MaterializationEvent>;
    assetSelection?: Maybe<Array<AssetKey>>;
    assets: Array<Asset>;
    canTerminate: Scalars["Boolean"]["output"];
    /**
     *
     *         Captured logs are the stdout/stderr logs for a given file key within the run
     *
     */
    capturedLogs: CapturedLogs;
    creationTime: Scalars["Float"]["output"];
    endTime?: Maybe<Scalars["Float"]["output"]>;
    eventConnection: EventConnection;
    executionPlan?: Maybe<ExecutionPlan>;
    hasConcurrencyKeySlots: Scalars["Boolean"]["output"];
    hasDeletePermission: Scalars["Boolean"]["output"];
    hasReExecutePermission: Scalars["Boolean"]["output"];
    hasRunMetricsEnabled: Scalars["Boolean"]["output"];
    hasTerminatePermission: Scalars["Boolean"]["output"];
    hasUnconstrainedRootNodes: Scalars["Boolean"]["output"];
    id: Scalars["ID"]["output"];
    jobName: Scalars["String"]["output"];
    mode: Scalars["String"]["output"];
    parentPipelineSnapshotId?: Maybe<Scalars["String"]["output"]>;
    parentRunId?: Maybe<Scalars["String"]["output"]>;
    pipeline: PipelineReference;
    pipelineName: Scalars["String"]["output"];
    pipelineSnapshotId?: Maybe<Scalars["String"]["output"]>;
    repositoryOrigin?: Maybe<RepositoryOrigin>;
    resolvedOpSelection?: Maybe<Array<Scalars["String"]["output"]>>;
    rootConcurrencyKeys?: Maybe<Array<Scalars["String"]["output"]>>;
    rootRunId?: Maybe<Scalars["String"]["output"]>;
    runConfig: Scalars["RunConfigData"]["output"];
    runConfigYaml: Scalars["String"]["output"];
    runId: Scalars["String"]["output"];
    /** Included to comply with RunsFeedEntry interface. Duplicate of status. */
    runStatus: RunStatus;
    solidSelection?: Maybe<Array<Scalars["String"]["output"]>>;
    startTime?: Maybe<Scalars["Float"]["output"]>;
    stats: RunStatsSnapshotOrError;
    status: RunStatus;
    stepKeysToExecute?: Maybe<Array<Scalars["String"]["output"]>>;
    stepStats: Array<RunStepStats>;
    tags: Array<PipelineTag>;
    updateTime?: Maybe<Scalars["Float"]["output"]>;
  };

export type RunCapturedLogsArgs = {
  fileKey: Scalars["String"]["input"];
};

export type RunEventConnectionArgs = {
  afterCursor?: InputMaybe<Scalars["String"]["input"]>;
  limit?: InputMaybe<Scalars["Int"]["input"]>;
};

export type RunCanceledEvent = ErrorEvent &
  MessageEvent &
  RunEvent & {
    __typename?: "RunCanceledEvent";
    error?: Maybe<PythonError>;
    eventType?: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars["String"]["output"];
    pipelineName: Scalars["String"]["output"];
    runId: Scalars["String"]["output"];
    solidHandleID?: Maybe<Scalars["String"]["output"]>;
    stepKey?: Maybe<Scalars["String"]["output"]>;
    timestamp: Scalars["String"]["output"];
  };

export type RunCancelingEvent = MessageEvent &
  RunEvent & {
    __typename?: "RunCancelingEvent";
    eventType?: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars["String"]["output"];
    pipelineName: Scalars["String"]["output"];
    runId: Scalars["String"]["output"];
    solidHandleID?: Maybe<Scalars["String"]["output"]>;
    stepKey?: Maybe<Scalars["String"]["output"]>;
    timestamp: Scalars["String"]["output"];
  };

/**
 * The run config schema represents the all the config type
 *         information given a certain execution selection and mode of execution of that
 *         selection. All config interactions (e.g. checking config validity, fetching
 *         all config types, fetching in a particular config type) should be done
 *         through this type
 */
export type RunConfigSchema = {
  __typename?: "RunConfigSchema";
  /**
   * Fetch all the named config types that are in the schema. Useful
   *         for things like a type browser UI, or for fetching all the types are in the
   *         scope of a document so that the index can be built for the autocompleting editor.
   *
   */
  allConfigTypes: Array<ConfigType>;
  /**
   * Parse a particular run config result. The return value
   *         either indicates that the validation succeeded by returning
   *         `PipelineConfigValidationValid` or that there are configuration errors
   *         by returning `RunConfigValidationInvalid' which containers a list errors
   *         so that can be rendered for the user
   */
  isRunConfigValid: PipelineConfigValidationResult;
  /**
   * Fetch the root environment type. Concretely this is the type that
   *         is in scope at the root of configuration document for a particular execution selection.
   *         It is the type that is in scope initially with a blank config editor.
   */
  rootConfigType: ConfigType;
  /**
   * The default configuration for this run in yaml. This is
   *         so that the client does not have to parse JSON client side and assemble
   *         it into a single yaml document.
   */
  rootDefaultYaml: Scalars["String"]["output"];
};

/**
 * The run config schema represents the all the config type
 *         information given a certain execution selection and mode of execution of that
 *         selection. All config interactions (e.g. checking config validity, fetching
 *         all config types, fetching in a particular config type) should be done
 *         through this type
 */
export type RunConfigSchemaIsRunConfigValidArgs = {
  runConfigData?: InputMaybe<Scalars["RunConfigData"]["input"]>;
};

export type RunConfigSchemaOrError =
  | InvalidSubsetError
  | ModeNotFoundError
  | PipelineNotFoundError
  | PythonError
  | RunConfigSchema;

export type RunConfigValidationInvalid = PipelineConfigValidationInvalid & {
  __typename?: "RunConfigValidationInvalid";
  errors: Array<PipelineConfigValidationError>;
  pipelineName: Scalars["String"]["output"];
};

export type RunConflict = Error &
  PipelineRunConflict & {
    __typename?: "RunConflict";
    message: Scalars["String"]["output"];
  };

export type RunDequeuedEvent = MessageEvent &
  RunEvent & {
    __typename?: "RunDequeuedEvent";
    eventType?: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars["String"]["output"];
    pipelineName: Scalars["String"]["output"];
    runId: Scalars["String"]["output"];
    solidHandleID?: Maybe<Scalars["String"]["output"]>;
    stepKey?: Maybe<Scalars["String"]["output"]>;
    timestamp: Scalars["String"]["output"];
  };

export type RunEnqueuedEvent = MessageEvent &
  RunEvent & {
    __typename?: "RunEnqueuedEvent";
    eventType?: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars["String"]["output"];
    pipelineName: Scalars["String"]["output"];
    runId: Scalars["String"]["output"];
    solidHandleID?: Maybe<Scalars["String"]["output"]>;
    stepKey?: Maybe<Scalars["String"]["output"]>;
    timestamp: Scalars["String"]["output"];
  };

export type RunEvent = {
  pipelineName: Scalars["String"]["output"];
};

export type RunFailureEvent = ErrorEvent &
  MessageEvent &
  RunEvent & {
    __typename?: "RunFailureEvent";
    error?: Maybe<PythonError>;
    eventType?: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars["String"]["output"];
    pipelineName: Scalars["String"]["output"];
    runId: Scalars["String"]["output"];
    solidHandleID?: Maybe<Scalars["String"]["output"]>;
    stepKey?: Maybe<Scalars["String"]["output"]>;
    timestamp: Scalars["String"]["output"];
  };

export type RunGroup = {
  __typename?: "RunGroup";
  rootRunId: Scalars["String"]["output"];
  runs?: Maybe<Array<Maybe<Run>>>;
};

export type RunGroupNotFoundError = Error & {
  __typename?: "RunGroupNotFoundError";
  message: Scalars["String"]["output"];
  runId: Scalars["String"]["output"];
};

export type RunGroupOrError = PythonError | RunGroup | RunGroupNotFoundError;

export type RunGroups = {
  __typename?: "RunGroups";
  results: Array<RunGroup>;
};

export type RunIds = {
  __typename?: "RunIds";
  results: Array<Scalars["String"]["output"]>;
};

export type RunIdsOrError =
  | InvalidPipelineRunsFilterError
  | PythonError
  | RunIds;

export type RunLauncher = {
  __typename?: "RunLauncher";
  name: Scalars["String"]["output"];
};

export type RunMarker = {
  __typename?: "RunMarker";
  endTime?: Maybe<Scalars["Float"]["output"]>;
  startTime?: Maybe<Scalars["Float"]["output"]>;
};

export type RunNotFoundError = Error &
  PipelineRunNotFoundError & {
    __typename?: "RunNotFoundError";
    message: Scalars["String"]["output"];
    runId: Scalars["String"]["output"];
  };

export type RunOrError = PythonError | Run | RunNotFoundError;

export type RunQueueConfig = {
  __typename?: "RunQueueConfig";
  isOpConcurrencyAware?: Maybe<Scalars["Boolean"]["output"]>;
  maxConcurrentRuns: Scalars["Int"]["output"];
  tagConcurrencyLimitsYaml?: Maybe<Scalars["String"]["output"]>;
};

export type RunRequest = {
  __typename?: "RunRequest";
  assetSelection?: Maybe<Array<AssetKey>>;
  jobName?: Maybe<Scalars["String"]["output"]>;
  runConfigYaml: Scalars["String"]["output"];
  runKey?: Maybe<Scalars["String"]["output"]>;
  tags: Array<PipelineTag>;
};

export type RunStartEvent = MessageEvent &
  RunEvent & {
    __typename?: "RunStartEvent";
    eventType?: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars["String"]["output"];
    pipelineName: Scalars["String"]["output"];
    runId: Scalars["String"]["output"];
    solidHandleID?: Maybe<Scalars["String"]["output"]>;
    stepKey?: Maybe<Scalars["String"]["output"]>;
    timestamp: Scalars["String"]["output"];
  };

export type RunStartingEvent = MessageEvent &
  RunEvent & {
    __typename?: "RunStartingEvent";
    eventType?: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars["String"]["output"];
    pipelineName: Scalars["String"]["output"];
    runId: Scalars["String"]["output"];
    solidHandleID?: Maybe<Scalars["String"]["output"]>;
    stepKey?: Maybe<Scalars["String"]["output"]>;
    timestamp: Scalars["String"]["output"];
  };

export type RunStatsSnapshot = PipelineRunStatsSnapshot & {
  __typename?: "RunStatsSnapshot";
  endTime?: Maybe<Scalars["Float"]["output"]>;
  enqueuedTime?: Maybe<Scalars["Float"]["output"]>;
  expectations: Scalars["Int"]["output"];
  id: Scalars["String"]["output"];
  launchTime?: Maybe<Scalars["Float"]["output"]>;
  materializations: Scalars["Int"]["output"];
  runId: Scalars["String"]["output"];
  startTime?: Maybe<Scalars["Float"]["output"]>;
  stepsFailed: Scalars["Int"]["output"];
  stepsSucceeded: Scalars["Int"]["output"];
};

export type RunStatsSnapshotOrError = PythonError | RunStatsSnapshot;

/** The status of run execution. */
export enum RunStatus {
  /** Runs that have been canceled before completion. */
  Canceled = "CANCELED",
  /** Runs that are in-progress and pending to be canceled. */
  Canceling = "CANCELING",
  /** Runs that have failed to complete. */
  Failure = "FAILURE",
  /** Runs that are managed outside of the Dagster control plane. */
  Managed = "MANAGED",
  /** Runs that have been created, but not yet submitted for launch. */
  NotStarted = "NOT_STARTED",
  /** Runs waiting to be launched by the Dagster Daemon. */
  Queued = "QUEUED",
  /** Runs that have been launched and execution has started. */
  Started = "STARTED",
  /** Runs that have been launched, but execution has not yet started. */
  Starting = "STARTING",
  /** Runs that have successfully completed. */
  Success = "SUCCESS",
}

export type RunStepStats = PipelineRunStepStats & {
  __typename?: "RunStepStats";
  attempts: Array<RunMarker>;
  endTime?: Maybe<Scalars["Float"]["output"]>;
  expectationResults: Array<ExpectationResult>;
  markers: Array<RunMarker>;
  materializations: Array<MaterializationEvent>;
  runId: Scalars["String"]["output"];
  startTime?: Maybe<Scalars["Float"]["output"]>;
  status?: Maybe<StepEventStatus>;
  stepKey: Scalars["String"]["output"];
};

export type RunSuccessEvent = MessageEvent &
  RunEvent & {
    __typename?: "RunSuccessEvent";
    eventType?: Maybe<DagsterEventType>;
    level: LogLevel;
    message: Scalars["String"]["output"];
    pipelineName: Scalars["String"]["output"];
    runId: Scalars["String"]["output"];
    solidHandleID?: Maybe<Scalars["String"]["output"]>;
    stepKey?: Maybe<Scalars["String"]["output"]>;
    timestamp: Scalars["String"]["output"];
  };

export type RunTagKeys = {
  __typename?: "RunTagKeys";
  keys: Array<Scalars["String"]["output"]>;
};

export type RunTagKeysOrError = PythonError | RunTagKeys;

export type RunTags = {
  __typename?: "RunTags";
  tags: Array<PipelineTagAndValues>;
};

export type RunTagsOrError = PythonError | RunTags;

export type Runs = PipelineRuns & {
  __typename?: "Runs";
  count?: Maybe<Scalars["Int"]["output"]>;
  results: Array<Run>;
};

export type RunsFeedConnection = {
  __typename?: "RunsFeedConnection";
  cursor: Scalars["String"]["output"];
  hasMore: Scalars["Boolean"]["output"];
  results: Array<RunsFeedEntry>;
};

export type RunsFeedConnectionOrError = PythonError | RunsFeedConnection;

export type RunsFeedCount = {
  __typename?: "RunsFeedCount";
  count: Scalars["Int"]["output"];
};

export type RunsFeedCountOrError = PythonError | RunsFeedCount;

export type RunsFeedEntry = {
  assetCheckSelection?: Maybe<Array<AssetCheckhandle>>;
  assetSelection?: Maybe<Array<AssetKey>>;
  creationTime: Scalars["Float"]["output"];
  endTime?: Maybe<Scalars["Float"]["output"]>;
  id: Scalars["ID"]["output"];
  jobName?: Maybe<Scalars["String"]["output"]>;
  runStatus?: Maybe<RunStatus>;
  startTime?: Maybe<Scalars["Float"]["output"]>;
  tags: Array<PipelineTag>;
};

/**
 * Configure how runs and backfills are represented in the feed.
 *
 * ROOTS: Return root-level runs and backfills
 * RUNS: Return runs only, including runs within backfills
 * BACKFILLS: Return backfills only
 */
export enum RunsFeedView {
  Backfills = "BACKFILLS",
  Roots = "ROOTS",
  Runs = "RUNS",
}

/** This type represents a filter on Dagster runs. */
export type RunsFilter = {
  createdAfter?: InputMaybe<Scalars["Float"]["input"]>;
  createdBefore?: InputMaybe<Scalars["Float"]["input"]>;
  mode?: InputMaybe<Scalars["String"]["input"]>;
  pipelineName?: InputMaybe<Scalars["String"]["input"]>;
  runIds?: InputMaybe<Array<InputMaybe<Scalars["String"]["input"]>>>;
  snapshotId?: InputMaybe<Scalars["String"]["input"]>;
  statuses?: InputMaybe<Array<RunStatus>>;
  tags?: InputMaybe<Array<ExecutionTag>>;
  updatedAfter?: InputMaybe<Scalars["Float"]["input"]>;
  updatedBefore?: InputMaybe<Scalars["Float"]["input"]>;
};

export type RunsOrError = InvalidPipelineRunsFilterError | PythonError | Runs;

export type RuntimeMismatchConfigError = PipelineConfigValidationError & {
  __typename?: "RuntimeMismatchConfigError";
  message: Scalars["String"]["output"];
  path: Array<Scalars["String"]["output"]>;
  reason: EvaluationErrorReason;
  stack: EvaluationStack;
  valueRep?: Maybe<Scalars["String"]["output"]>;
};

export type ScalarUnionConfigType = ConfigType & {
  __typename?: "ScalarUnionConfigType";
  description?: Maybe<Scalars["String"]["output"]>;
  isSelector: Scalars["Boolean"]["output"];
  key: Scalars["String"]["output"];
  nonScalarType: ConfigType;
  nonScalarTypeKey: Scalars["String"]["output"];
  /**
   *
   * This is an odd and problematic field. It recursively goes down to
   * get all the types contained within a type. The case where it is horrible
   * are dictionaries and it recurses all the way down to the leaves. This means
   * that in a case where one is fetching all the types and then all the inner
   * types keys for those types, we are returning O(N^2) type keys, which
   * can cause awful performance for large schemas. When you have access
   * to *all* the types, you should instead only use the type_param_keys
   * field for closed generic types and manually navigate down the to
   * field types client-side.
   *
   * Where it is useful is when you are fetching types independently and
   * want to be able to render them, but without fetching the entire schema.
   *
   * We use this capability when rendering the sidebar.
   *
   */
  recursiveConfigTypes: Array<ConfigType>;
  scalarType: ConfigType;
  scalarTypeKey: Scalars["String"]["output"];
  /**
   *
   * This returns the keys for type parameters of any closed generic type,
   * (e.g. List, Optional). This should be used for reconstructing and
   * navigating the full schema client-side and not innerTypes.
   *
   */
  typeParamKeys: Array<Scalars["String"]["output"]>;
};

export type Schedule = {
  __typename?: "Schedule";
  assetSelection?: Maybe<AssetSelection>;
  canReset: Scalars["Boolean"]["output"];
  cronSchedule: Scalars["String"]["output"];
  defaultStatus: InstigationStatus;
  description?: Maybe<Scalars["String"]["output"]>;
  executionTimezone?: Maybe<Scalars["String"]["output"]>;
  futureTick: DryRunInstigationTick;
  futureTicks: DryRunInstigationTicks;
  id: Scalars["ID"]["output"];
  metadataEntries: Array<MetadataEntry>;
  mode: Scalars["String"]["output"];
  name: Scalars["String"]["output"];
  partitionSet?: Maybe<PartitionSet>;
  pipelineName: Scalars["String"]["output"];
  potentialTickTimestamps: Array<Scalars["Float"]["output"]>;
  scheduleState: InstigationState;
  solidSelection?: Maybe<Array<Maybe<Scalars["String"]["output"]>>>;
  tags: Array<DefinitionTag>;
};

export type ScheduleFutureTickArgs = {
  tickTimestamp: Scalars["Int"]["input"];
};

export type ScheduleFutureTicksArgs = {
  cursor?: InputMaybe<Scalars["Float"]["input"]>;
  limit?: InputMaybe<Scalars["Int"]["input"]>;
  until?: InputMaybe<Scalars["Float"]["input"]>;
};

export type SchedulePotentialTickTimestampsArgs = {
  lowerLimit?: InputMaybe<Scalars["Int"]["input"]>;
  startTimestamp?: InputMaybe<Scalars["Float"]["input"]>;
  upperLimit?: InputMaybe<Scalars["Int"]["input"]>;
};

export type ScheduleData = {
  __typename?: "ScheduleData";
  cronSchedule: Scalars["String"]["output"];
  startTimestamp?: Maybe<Scalars["Float"]["output"]>;
};

export type ScheduleDryRunResult =
  | DryRunInstigationTick
  | PythonError
  | ScheduleNotFoundError;

export type ScheduleMutationResult =
  | PythonError
  | ScheduleNotFoundError
  | ScheduleStateResult
  | UnauthorizedError;

export type ScheduleNotFoundError = Error & {
  __typename?: "ScheduleNotFoundError";
  message: Scalars["String"]["output"];
  scheduleName: Scalars["String"]["output"];
};

export type ScheduleOrError = PythonError | Schedule | ScheduleNotFoundError;

/** This type represents the fields necessary to identify a schedule. */
export type ScheduleSelector = {
  repositoryLocationName: Scalars["String"]["input"];
  repositoryName: Scalars["String"]["input"];
  scheduleName: Scalars["String"]["input"];
};

export type ScheduleStateResult = {
  __typename?: "ScheduleStateResult";
  scheduleState: InstigationState;
};

export enum ScheduleStatus {
  Ended = "ENDED",
  Running = "RUNNING",
  Stopped = "STOPPED",
}

export type ScheduleTick = {
  __typename?: "ScheduleTick";
  status: InstigationTickStatus;
  tickId: Scalars["String"]["output"];
  tickSpecificData?: Maybe<ScheduleTickSpecificData>;
  timestamp: Scalars["Float"]["output"];
};

export type ScheduleTickFailureData = {
  __typename?: "ScheduleTickFailureData";
  error: PythonError;
};

export type ScheduleTickSpecificData =
  | ScheduleTickFailureData
  | ScheduleTickSuccessData;

export type ScheduleTickSuccessData = {
  __typename?: "ScheduleTickSuccessData";
  run?: Maybe<Run>;
};

export type Scheduler = {
  __typename?: "Scheduler";
  schedulerClass?: Maybe<Scalars["String"]["output"]>;
};

export type SchedulerNotDefinedError = Error & {
  __typename?: "SchedulerNotDefinedError";
  message: Scalars["String"]["output"];
};

export type SchedulerOrError =
  | PythonError
  | Scheduler
  | SchedulerNotDefinedError;

export type Schedules = {
  __typename?: "Schedules";
  results: Array<Schedule>;
};

export type SchedulesOrError =
  | PythonError
  | RepositoryNotFoundError
  | Schedules;

export type SelectorTypeConfigError = PipelineConfigValidationError & {
  __typename?: "SelectorTypeConfigError";
  incomingFields: Array<Scalars["String"]["output"]>;
  message: Scalars["String"]["output"];
  path: Array<Scalars["String"]["output"]>;
  reason: EvaluationErrorReason;
  stack: EvaluationStack;
};

export type Sensor = {
  __typename?: "Sensor";
  assetSelection?: Maybe<AssetSelection>;
  canReset: Scalars["Boolean"]["output"];
  defaultStatus: InstigationStatus;
  description?: Maybe<Scalars["String"]["output"]>;
  id: Scalars["ID"]["output"];
  jobOriginId: Scalars["String"]["output"];
  metadata: SensorMetadata;
  metadataEntries: Array<MetadataEntry>;
  minIntervalSeconds: Scalars["Int"]["output"];
  name: Scalars["String"]["output"];
  nextTick?: Maybe<DryRunInstigationTick>;
  sensorState: InstigationState;
  sensorType: SensorType;
  tags: Array<DefinitionTag>;
  targets?: Maybe<Array<Target>>;
};

export type SensorData = {
  __typename?: "SensorData";
  lastCursor?: Maybe<Scalars["String"]["output"]>;
  lastRunKey?: Maybe<Scalars["String"]["output"]>;
  lastTickTimestamp?: Maybe<Scalars["Float"]["output"]>;
};

export type SensorDryRunResult =
  | DryRunInstigationTick
  | PythonError
  | SensorNotFoundError;

export type SensorMetadata = {
  __typename?: "SensorMetadata";
  assetKeys?: Maybe<Array<AssetKey>>;
};

export type SensorNotFoundError = Error & {
  __typename?: "SensorNotFoundError";
  message: Scalars["String"]["output"];
  sensorName: Scalars["String"]["output"];
};

export type SensorOrError =
  | PythonError
  | Sensor
  | SensorNotFoundError
  | UnauthorizedError;

/** This type represents the fields necessary to identify a sensor. */
export type SensorSelector = {
  repositoryLocationName: Scalars["String"]["input"];
  repositoryName: Scalars["String"]["input"];
  sensorName: Scalars["String"]["input"];
};

/** An enumeration. */
export enum SensorType {
  Asset = "ASSET",
  Automation = "AUTOMATION",
  AutoMaterialize = "AUTO_MATERIALIZE",
  FreshnessPolicy = "FRESHNESS_POLICY",
  MultiAsset = "MULTI_ASSET",
  RunStatus = "RUN_STATUS",
  Standard = "STANDARD",
  Unknown = "UNKNOWN",
}

export type Sensors = {
  __typename?: "Sensors";
  results: Array<Sensor>;
};

export type SensorsOrError = PythonError | RepositoryNotFoundError | Sensors;

/** Set a cursor for a sensor to track state across evaluations. */
export type SetSensorCursorMutation = {
  __typename?: "SetSensorCursorMutation";
  Output: SensorOrError;
};

/** Shuts down a code location server. */
export type ShutdownRepositoryLocationMutation = {
  __typename?: "ShutdownRepositoryLocationMutation";
  Output: ShutdownRepositoryLocationMutationResult;
};

/** The output from shutting down a code location server. */
export type ShutdownRepositoryLocationMutationResult =
  | PythonError
  | RepositoryLocationNotFound
  | ShutdownRepositoryLocationSuccess
  | UnauthorizedError;

/** Output indicating that a code location server was shut down. */
export type ShutdownRepositoryLocationSuccess = {
  __typename?: "ShutdownRepositoryLocationSuccess";
  repositoryLocationName: Scalars["String"]["output"];
};

export type Solid = {
  __typename?: "Solid";
  definition: ISolidDefinition;
  inputs: Array<Input>;
  isDynamicMapped: Scalars["Boolean"]["output"];
  name: Scalars["String"]["output"];
  outputs: Array<Output>;
};

export type SolidContainer = {
  description?: Maybe<Scalars["String"]["output"]>;
  id: Scalars["ID"]["output"];
  modes: Array<Mode>;
  name: Scalars["String"]["output"];
  solidHandle?: Maybe<SolidHandle>;
  solidHandles: Array<SolidHandle>;
  solids: Array<Solid>;
};

export type SolidContainerSolidHandleArgs = {
  handleID: Scalars["String"]["input"];
};

export type SolidContainerSolidHandlesArgs = {
  parentHandleID?: InputMaybe<Scalars["String"]["input"]>;
};

export type SolidDefinition = ISolidDefinition & {
  __typename?: "SolidDefinition";
  assetNodes: Array<AssetNode>;
  configField?: Maybe<ConfigTypeField>;
  description?: Maybe<Scalars["String"]["output"]>;
  inputDefinitions: Array<InputDefinition>;
  metadata: Array<MetadataItemDefinition>;
  name: Scalars["String"]["output"];
  outputDefinitions: Array<OutputDefinition>;
  pool?: Maybe<Scalars["String"]["output"]>;
  pools: Array<Scalars["String"]["output"]>;
  requiredResources: Array<ResourceRequirement>;
};

export type SolidHandle = {
  __typename?: "SolidHandle";
  handleID: Scalars["String"]["output"];
  parent?: Maybe<SolidHandle>;
  solid: Solid;
  stepStats?: Maybe<SolidStepStatsOrError>;
};

export type SolidHandleStepStatsArgs = {
  limit?: InputMaybe<Scalars["Int"]["input"]>;
};

export type SolidStepStatsConnection = {
  __typename?: "SolidStepStatsConnection";
  nodes: Array<RunStepStats>;
};

export type SolidStepStatsOrError =
  | SolidStepStatsConnection
  | SolidStepStatusUnavailableError;

export type SolidStepStatusUnavailableError = Error & {
  __typename?: "SolidStepStatusUnavailableError";
  message: Scalars["String"]["output"];
};

export type SourceLocation = LocalFileCodeReference | UrlCodeReference;

export type SpecificPartitionAssetConditionEvaluationNode = {
  __typename?: "SpecificPartitionAssetConditionEvaluationNode";
  childUniqueIds: Array<Scalars["String"]["output"]>;
  description: Scalars["String"]["output"];
  metadataEntries: Array<MetadataEntry>;
  status: AssetConditionEvaluationStatus;
  uniqueId: Scalars["String"]["output"];
};

export type StaleCause = {
  __typename?: "StaleCause";
  category: StaleCauseCategory;
  dependency?: Maybe<AssetKey>;
  dependencyPartitionKey?: Maybe<Scalars["String"]["output"]>;
  key: AssetKey;
  partitionKey?: Maybe<Scalars["String"]["output"]>;
  reason: Scalars["String"]["output"];
};

/** An enumeration. */
export enum StaleCauseCategory {
  Code = "CODE",
  Data = "DATA",
  Dependencies = "DEPENDENCIES",
}

/** An enumeration. */
export enum StaleStatus {
  Fresh = "FRESH",
  Missing = "MISSING",
  Stale = "STALE",
}

/** Enable a schedule to launch runs for a job at a fixed interval. */
export type StartScheduleMutation = {
  __typename?: "StartScheduleMutation";
  Output: ScheduleMutationResult;
};

export type StepEvent = {
  solidHandleID?: Maybe<Scalars["String"]["output"]>;
  stepKey?: Maybe<Scalars["String"]["output"]>;
};

export enum StepEventStatus {
  Failure = "FAILURE",
  InProgress = "IN_PROGRESS",
  Skipped = "SKIPPED",
  Success = "SUCCESS",
}

export type StepExecution = {
  marshalledInputs?: InputMaybe<Array<MarshalledInput>>;
  marshalledOutputs?: InputMaybe<Array<MarshalledOutput>>;
  stepKey: Scalars["String"]["input"];
};

export type StepExpectationResultEvent = MessageEvent &
  StepEvent & {
    __typename?: "StepExpectationResultEvent";
    eventType?: Maybe<DagsterEventType>;
    expectationResult: ExpectationResult;
    level: LogLevel;
    message: Scalars["String"]["output"];
    runId: Scalars["String"]["output"];
    solidHandleID?: Maybe<Scalars["String"]["output"]>;
    stepKey?: Maybe<Scalars["String"]["output"]>;
    timestamp: Scalars["String"]["output"];
  };

export enum StepKind {
  /** This is a user-defined computation step */
  Compute = "COMPUTE",
  /** This is a collect step that is not yet resolved */
  UnresolvedCollect = "UNRESOLVED_COLLECT",
  /** This is a mapped step that has not yet been resolved */
  UnresolvedMapped = "UNRESOLVED_MAPPED",
}

export type StepOutputHandle = {
  outputName: Scalars["String"]["input"];
  stepKey: Scalars["String"]["input"];
};

export type StepWorkerStartedEvent = DisplayableEvent &
  MarkerEvent &
  MessageEvent &
  StepEvent & {
    __typename?: "StepWorkerStartedEvent";
    description?: Maybe<Scalars["String"]["output"]>;
    eventType?: Maybe<DagsterEventType>;
    label?: Maybe<Scalars["String"]["output"]>;
    level: LogLevel;
    markerEnd?: Maybe<Scalars["String"]["output"]>;
    markerStart?: Maybe<Scalars["String"]["output"]>;
    message: Scalars["String"]["output"];
    metadataEntries: Array<MetadataEntry>;
    runId: Scalars["String"]["output"];
    solidHandleID?: Maybe<Scalars["String"]["output"]>;
    stepKey?: Maybe<Scalars["String"]["output"]>;
    timestamp: Scalars["String"]["output"];
  };

export type StepWorkerStartingEvent = DisplayableEvent &
  MarkerEvent &
  MessageEvent &
  StepEvent & {
    __typename?: "StepWorkerStartingEvent";
    description?: Maybe<Scalars["String"]["output"]>;
    eventType?: Maybe<DagsterEventType>;
    label?: Maybe<Scalars["String"]["output"]>;
    level: LogLevel;
    markerEnd?: Maybe<Scalars["String"]["output"]>;
    markerStart?: Maybe<Scalars["String"]["output"]>;
    message: Scalars["String"]["output"];
    metadataEntries: Array<MetadataEntry>;
    runId: Scalars["String"]["output"];
    solidHandleID?: Maybe<Scalars["String"]["output"]>;
    stepKey?: Maybe<Scalars["String"]["output"]>;
    timestamp: Scalars["String"]["output"];
  };

/** Disable a schedule from launching runs for a job. */
export type StopRunningScheduleMutation = {
  __typename?: "StopRunningScheduleMutation";
  Output: ScheduleMutationResult;
};

/** Disable a sensor from launching runs for a job. */
export type StopSensorMutation = {
  __typename?: "StopSensorMutation";
  Output: StopSensorMutationResultOrError;
};

export type StopSensorMutationResult = {
  __typename?: "StopSensorMutationResult";
  instigationState?: Maybe<InstigationState>;
};

export type StopSensorMutationResultOrError =
  | PythonError
  | StopSensorMutationResult
  | UnauthorizedError;

/** The root for all subscriptions to retrieve real-time data from the Dagster instance. */
export type Subscription = {
  __typename?: "Subscription";
  /** Retrieve real-time compute logs. */
  capturedLogs: CapturedLogs;
  /** Retrieve real-time events when a location in the workspace undergoes a state change. */
  locationStateChangeEvents: LocationStateChangeSubscription;
  /** Retrieve real-time event logs after applying a filter on run id and cursor. */
  pipelineRunLogs: PipelineRunLogsSubscriptionPayload;
};

/** The root for all subscriptions to retrieve real-time data from the Dagster instance. */
export type SubscriptionCapturedLogsArgs = {
  cursor?: InputMaybe<Scalars["String"]["input"]>;
  logKey: Array<Scalars["String"]["input"]>;
};

/** The root for all subscriptions to retrieve real-time data from the Dagster instance. */
export type SubscriptionPipelineRunLogsArgs = {
  cursor?: InputMaybe<Scalars["String"]["input"]>;
  runId: Scalars["ID"]["input"];
};

export type Table = {
  __typename?: "Table";
  records: Array<Scalars["String"]["output"]>;
  schema: TableSchema;
};

export type TableColumn = {
  __typename?: "TableColumn";
  constraints: TableColumnConstraints;
  description?: Maybe<Scalars["String"]["output"]>;
  name: Scalars["String"]["output"];
  tags: Array<DefinitionTag>;
  type: Scalars["String"]["output"];
};

export type TableColumnConstraints = {
  __typename?: "TableColumnConstraints";
  nullable: Scalars["Boolean"]["output"];
  other: Array<Scalars["String"]["output"]>;
  unique: Scalars["Boolean"]["output"];
};

export type TableColumnDep = {
  __typename?: "TableColumnDep";
  assetKey: AssetKey;
  columnName: Scalars["String"]["output"];
};

export type TableColumnLineageEntry = {
  __typename?: "TableColumnLineageEntry";
  columnDeps: Array<TableColumnDep>;
  columnName: Scalars["String"]["output"];
};

export type TableColumnLineageMetadataEntry = MetadataEntry & {
  __typename?: "TableColumnLineageMetadataEntry";
  description?: Maybe<Scalars["String"]["output"]>;
  label: Scalars["String"]["output"];
  lineage: Array<TableColumnLineageEntry>;
};

export type TableConstraints = {
  __typename?: "TableConstraints";
  other: Array<Scalars["String"]["output"]>;
};

export type TableMetadataEntry = MetadataEntry & {
  __typename?: "TableMetadataEntry";
  description?: Maybe<Scalars["String"]["output"]>;
  label: Scalars["String"]["output"];
  table: Table;
};

export type TableSchema = {
  __typename?: "TableSchema";
  columns: Array<TableColumn>;
  constraints?: Maybe<TableConstraints>;
};

export type TableSchemaMetadataEntry = MetadataEntry & {
  __typename?: "TableSchemaMetadataEntry";
  description?: Maybe<Scalars["String"]["output"]>;
  label: Scalars["String"]["output"];
  schema: TableSchema;
};

export type TagInput = {
  key: Scalars["String"]["input"];
  value: Scalars["String"]["input"];
};

export type Target = {
  __typename?: "Target";
  mode: Scalars["String"]["output"];
  pipelineName: Scalars["String"]["output"];
  solidSelection?: Maybe<Array<Scalars["String"]["output"]>>;
};

export type TeamAssetOwner = {
  __typename?: "TeamAssetOwner";
  team: Scalars["String"]["output"];
};

/** Interface indicating that a run failed to terminate. */
export type TerminatePipelineExecutionFailure = {
  message: Scalars["String"]["output"];
  run: Run;
};

/** Interface indicating that a run was terminated. */
export type TerminatePipelineExecutionSuccess = {
  run: Run;
};

/** Output indicating that a run failed to terminate. */
export type TerminateRunFailure = TerminatePipelineExecutionFailure & {
  __typename?: "TerminateRunFailure";
  message: Scalars["String"]["output"];
  run: Run;
};

/** Terminates a run. */
export type TerminateRunMutation = {
  __typename?: "TerminateRunMutation";
  Output: TerminateRunResult;
};

/** The type of termination policy to use for a run. */
export enum TerminateRunPolicy {
  MarkAsCanceledImmediately = "MARK_AS_CANCELED_IMMEDIATELY",
  SafeTerminate = "SAFE_TERMINATE",
}

/** The output from a run termination. */
export type TerminateRunResult =
  | PythonError
  | RunNotFoundError
  | TerminateRunFailure
  | TerminateRunSuccess
  | UnauthorizedError;

/** Output indicating that a run was terminated. */
export type TerminateRunSuccess = TerminatePipelineExecutionSuccess & {
  __typename?: "TerminateRunSuccess";
  run: Run;
};

/** Indicates the runs that successfully terminated and those that failed to terminate. */
export type TerminateRunsResult = {
  __typename?: "TerminateRunsResult";
  terminateRunResults: Array<TerminateRunResult>;
};

/** The output from runs termination. */
export type TerminateRunsResultOrError = PythonError | TerminateRunsResult;

export type TestFields = {
  __typename?: "TestFields";
  alwaysException?: Maybe<Scalars["String"]["output"]>;
  asyncString?: Maybe<Scalars["String"]["output"]>;
};

export type TextMetadataEntry = MetadataEntry & {
  __typename?: "TextMetadataEntry";
  description?: Maybe<Scalars["String"]["output"]>;
  label: Scalars["String"]["output"];
  text: Scalars["String"]["output"];
};

export type TextRuleEvaluationData = {
  __typename?: "TextRuleEvaluationData";
  text?: Maybe<Scalars["String"]["output"]>;
};

export type TickEvaluation = {
  __typename?: "TickEvaluation";
  cursor?: Maybe<Scalars["String"]["output"]>;
  dynamicPartitionsRequests?: Maybe<Array<DynamicPartitionRequest>>;
  error?: Maybe<PythonError>;
  runRequests?: Maybe<Array<RunRequest>>;
  skipReason?: Maybe<Scalars["String"]["output"]>;
};

export type TimePartitionRangeStatus = {
  __typename?: "TimePartitionRangeStatus";
  endKey: Scalars["String"]["output"];
  endTime: Scalars["Float"]["output"];
  startKey: Scalars["String"]["output"];
  startTime: Scalars["Float"]["output"];
  status: PartitionRangeStatus;
};

export type TimePartitionStatuses = {
  __typename?: "TimePartitionStatuses";
  ranges: Array<TimePartitionRangeStatus>;
};

export type TimestampMetadataEntry = MetadataEntry & {
  __typename?: "TimestampMetadataEntry";
  description?: Maybe<Scalars["String"]["output"]>;
  label: Scalars["String"]["output"];
  timestamp: Scalars["Float"]["output"];
};

export type TypeCheck = DisplayableEvent & {
  __typename?: "TypeCheck";
  description?: Maybe<Scalars["String"]["output"]>;
  label?: Maybe<Scalars["String"]["output"]>;
  metadataEntries: Array<MetadataEntry>;
  success: Scalars["Boolean"]["output"];
};

export type UnauthorizedError = Error & {
  __typename?: "UnauthorizedError";
  message: Scalars["String"]["output"];
};

export type UnknownPipeline = PipelineReference & {
  __typename?: "UnknownPipeline";
  name: Scalars["String"]["output"];
  solidSelection?: Maybe<Array<Scalars["String"]["output"]>>;
};

export type UnpartitionedAssetConditionEvaluationNode = {
  __typename?: "UnpartitionedAssetConditionEvaluationNode";
  childUniqueIds: Array<Scalars["String"]["output"]>;
  description: Scalars["String"]["output"];
  endTimestamp?: Maybe<Scalars["Float"]["output"]>;
  metadataEntries: Array<MetadataEntry>;
  startTimestamp?: Maybe<Scalars["Float"]["output"]>;
  status: AssetConditionEvaluationStatus;
  uniqueId: Scalars["String"]["output"];
};

export type UnpartitionedAssetStatus = {
  __typename?: "UnpartitionedAssetStatus";
  assetKey: AssetKey;
  failed: Scalars["Boolean"]["output"];
  inProgress: Scalars["Boolean"]["output"];
  materialized: Scalars["Boolean"]["output"];
};

export type UnsupportedOperationError = Error & {
  __typename?: "UnsupportedOperationError";
  message: Scalars["String"]["output"];
};

export type UrlCodeReference = {
  __typename?: "UrlCodeReference";
  label?: Maybe<Scalars["String"]["output"]>;
  url: Scalars["String"]["output"];
};

export type UrlMetadataEntry = MetadataEntry & {
  __typename?: "UrlMetadataEntry";
  description?: Maybe<Scalars["String"]["output"]>;
  label: Scalars["String"]["output"];
  url: Scalars["String"]["output"];
};

/** A solid definition and its invocations within the repo. */
export type UsedSolid = {
  __typename?: "UsedSolid";
  definition: ISolidDefinition;
  invocations: Array<NodeInvocationSite>;
};

export type UserAssetOwner = {
  __typename?: "UserAssetOwner";
  email: Scalars["String"]["output"];
};

export type WaitingOnKeysRuleEvaluationData = {
  __typename?: "WaitingOnKeysRuleEvaluationData";
  waitingOnAssetKeys?: Maybe<Array<AssetKey>>;
};

export type Workspace = {
  __typename?: "Workspace";
  id: Scalars["String"]["output"];
  locationEntries: Array<WorkspaceLocationEntry>;
};

export type WorkspaceLocationEntry = {
  __typename?: "WorkspaceLocationEntry";
  displayMetadata: Array<RepositoryMetadata>;
  featureFlags: Array<FeatureFlag>;
  id: Scalars["ID"]["output"];
  loadStatus: RepositoryLocationLoadStatus;
  locationOrLoadError?: Maybe<RepositoryLocationOrLoadError>;
  name: Scalars["String"]["output"];
  permissions: Array<Permission>;
  updatedTimestamp: Scalars["Float"]["output"];
  versionKey: Scalars["String"]["output"];
};

export type WorkspaceLocationEntryOrError =
  | PythonError
  | WorkspaceLocationEntry;

export type WorkspaceLocationStatusEntries = {
  __typename?: "WorkspaceLocationStatusEntries";
  entries: Array<WorkspaceLocationStatusEntry>;
};

export type WorkspaceLocationStatusEntriesOrError =
  | PythonError
  | WorkspaceLocationStatusEntries;

export type WorkspaceLocationStatusEntry = {
  __typename?: "WorkspaceLocationStatusEntry";
  id: Scalars["ID"]["output"];
  loadStatus: RepositoryLocationLoadStatus;
  name: Scalars["String"]["output"];
  permissions: Array<Permission>;
  updateTimestamp: Scalars["Float"]["output"];
  versionKey: Scalars["String"]["output"];
};

export type WorkspaceOrError = PythonError | Workspace;

export type WrappingConfigType = {
  ofType: ConfigType;
};

export type WrappingDagsterType = {
  ofType: DagsterType;
};

export type _Service = {
  __typename?: "_Service";
  sdl: Scalars["String"]["output"];
};

export type AssetGraphQueryVariables = Exact<{ [key: string]: never }>;

export type AssetGraphQuery = {
  __typename?: "Query";
  assetNodes: Array<{
    __typename?: "AssetNode";
    assetKey: { __typename?: "AssetKey"; path: Array<string> };
    dependencyKeys: Array<{ __typename?: "AssetKey"; path: Array<string> }>;
  }>;
};

export type AssetMaterializedDataQueryVariables = Exact<{
  assetKeys?: InputMaybe<Array<AssetKeyInput> | AssetKeyInput>;
}>;

export type AssetMaterializedDataQuery = {
  __typename?: "Query";
  assetNodes: Array<{
    __typename?: "AssetNode";
    assetKey: { __typename?: "AssetKey"; path: Array<string> };
    partitionStats?: {
      __typename?: "PartitionStats";
      numFailed: number;
      numMaterialized: number;
      numMaterializing: number;
      numPartitions: number;
    } | null;
    assetPartitionStatuses:
      | { __typename?: "DefaultPartitionStatuses" }
      | { __typename?: "MultiPartitionStatuses" }
      | {
          __typename: "TimePartitionStatuses";
          ranges: Array<{
            __typename?: "TimePartitionRangeStatus";
            endKey: string;
            startKey: string;
            status: PartitionRangeStatus;
          }>;
        };
    assetMaterializations: Array<{
      __typename?: "MaterializationEvent";
      runOrError:
        | { __typename?: "PythonError" }
        | { __typename?: "Run"; endTime?: number | null }
        | { __typename?: "RunNotFoundError" };
    }>;
  }>;
};

export type TimeseriesMetricsByArtifactQueryVariables = Exact<{
  artifactIds?: InputMaybe<
    Array<Scalars["String"]["input"]> | Scalars["String"]["input"]
  >;
  metricIds?: InputMaybe<
    Array<Scalars["String"]["input"]> | Scalars["String"]["input"]
  >;
  startDate: Scalars["Oso_Date"]["input"];
  endDate: Scalars["Oso_Date"]["input"];
}>;

export type TimeseriesMetricsByArtifactQuery = {
  __typename?: "Query";
  oso_timeseriesMetricsByArtifactV0?: Array<{
    __typename?: "Oso_TimeseriesMetricsByArtifactV0";
    amount: any;
    artifactId: string;
    metricId: string;
    sampleDate: any;
    unit: string;
  }> | null;
  oso_artifactsV1?: Array<{
    __typename?: "Oso_ArtifactsV1";
    artifactId: string;
    artifactSource: string;
    artifactNamespace: string;
    artifactName: string;
  }> | null;
  oso_metricsV0?: Array<{
    __typename?: "Oso_MetricsV0";
    metricId: string;
    metricSource: string;
    metricNamespace: string;
    metricName: string;
    displayName: string;
    description: string;
  }> | null;
};

export type TimeseriesMetricsByProjectQueryVariables = Exact<{
  projectIds?: InputMaybe<
    Array<Scalars["String"]["input"]> | Scalars["String"]["input"]
  >;
  metricIds?: InputMaybe<
    Array<Scalars["String"]["input"]> | Scalars["String"]["input"]
  >;
  startDate: Scalars["Oso_Date"]["input"];
  endDate: Scalars["Oso_Date"]["input"];
}>;

export type TimeseriesMetricsByProjectQuery = {
  __typename?: "Query";
  oso_timeseriesMetricsByProjectV0?: Array<{
    __typename?: "Oso_TimeseriesMetricsByProjectV0";
    amount: any;
    metricId: string;
    projectId: string;
    sampleDate: any;
    unit: string;
  }> | null;
  oso_projectsV1?: Array<{
    __typename?: "Oso_ProjectsV1";
    projectId: string;
    projectSource: string;
    projectNamespace: string;
    projectName: string;
    displayName: string;
    description: string;
  }> | null;
  oso_metricsV0?: Array<{
    __typename?: "Oso_MetricsV0";
    metricId: string;
    metricSource: string;
    metricNamespace: string;
    metricName: string;
    displayName: string;
    description: string;
  }> | null;
};

export type TimeseriesMetricsByCollectionQueryVariables = Exact<{
  collectionIds?: InputMaybe<
    Array<Scalars["String"]["input"]> | Scalars["String"]["input"]
  >;
  metricIds?: InputMaybe<
    Array<Scalars["String"]["input"]> | Scalars["String"]["input"]
  >;
  startDate: Scalars["Oso_Date"]["input"];
  endDate: Scalars["Oso_Date"]["input"];
}>;

export type TimeseriesMetricsByCollectionQuery = {
  __typename?: "Query";
  oso_timeseriesMetricsByCollectionV0?: Array<{
    __typename?: "Oso_TimeseriesMetricsByCollectionV0";
    amount: any;
    metricId: string;
    collectionId: string;
    sampleDate: any;
    unit: string;
  }> | null;
  oso_collectionsV1?: Array<{
    __typename?: "Oso_CollectionsV1";
    collectionId: string;
    collectionSource: string;
    collectionNamespace: string;
    collectionName: string;
    displayName: string;
    description: string;
  }> | null;
  oso_metricsV0?: Array<{
    __typename?: "Oso_MetricsV0";
    metricId: string;
    metricSource: string;
    metricNamespace: string;
    metricName: string;
    displayName: string;
    description: string;
  }> | null;
};

export const AssetGraphDocument = {
  kind: "Document",
  definitions: [
    {
      kind: "OperationDefinition",
      operation: "query",
      name: { kind: "Name", value: "AssetGraph" },
      selectionSet: {
        kind: "SelectionSet",
        selections: [
          {
            kind: "Field",
            name: { kind: "Name", value: "assetNodes" },
            selectionSet: {
              kind: "SelectionSet",
              selections: [
                {
                  kind: "Field",
                  name: { kind: "Name", value: "assetKey" },
                  selectionSet: {
                    kind: "SelectionSet",
                    selections: [
                      { kind: "Field", name: { kind: "Name", value: "path" } },
                    ],
                  },
                },
                {
                  kind: "Field",
                  name: { kind: "Name", value: "dependencyKeys" },
                  selectionSet: {
                    kind: "SelectionSet",
                    selections: [
                      { kind: "Field", name: { kind: "Name", value: "path" } },
                    ],
                  },
                },
              ],
            },
          },
        ],
      },
    },
  ],
} as unknown as DocumentNode<AssetGraphQuery, AssetGraphQueryVariables>;
export const AssetMaterializedDataDocument = {
  kind: "Document",
  definitions: [
    {
      kind: "OperationDefinition",
      operation: "query",
      name: { kind: "Name", value: "AssetMaterializedData" },
      variableDefinitions: [
        {
          kind: "VariableDefinition",
          variable: {
            kind: "Variable",
            name: { kind: "Name", value: "assetKeys" },
          },
          type: {
            kind: "ListType",
            type: {
              kind: "NonNullType",
              type: {
                kind: "NamedType",
                name: { kind: "Name", value: "AssetKeyInput" },
              },
            },
          },
          defaultValue: {
            kind: "ObjectValue",
            fields: [
              {
                kind: "ObjectField",
                name: { kind: "Name", value: "path" },
                value: { kind: "StringValue", value: "", block: false },
              },
            ],
          },
        },
      ],
      selectionSet: {
        kind: "SelectionSet",
        selections: [
          {
            kind: "Field",
            name: { kind: "Name", value: "assetNodes" },
            arguments: [
              {
                kind: "Argument",
                name: { kind: "Name", value: "assetKeys" },
                value: {
                  kind: "Variable",
                  name: { kind: "Name", value: "assetKeys" },
                },
              },
            ],
            selectionSet: {
              kind: "SelectionSet",
              selections: [
                {
                  kind: "Field",
                  name: { kind: "Name", value: "assetKey" },
                  selectionSet: {
                    kind: "SelectionSet",
                    selections: [
                      { kind: "Field", name: { kind: "Name", value: "path" } },
                    ],
                  },
                },
                {
                  kind: "Field",
                  name: { kind: "Name", value: "partitionStats" },
                  selectionSet: {
                    kind: "SelectionSet",
                    selections: [
                      {
                        kind: "Field",
                        name: { kind: "Name", value: "numFailed" },
                      },
                      {
                        kind: "Field",
                        name: { kind: "Name", value: "numMaterialized" },
                      },
                      {
                        kind: "Field",
                        name: { kind: "Name", value: "numMaterializing" },
                      },
                      {
                        kind: "Field",
                        name: { kind: "Name", value: "numPartitions" },
                      },
                    ],
                  },
                },
                {
                  kind: "Field",
                  name: { kind: "Name", value: "assetPartitionStatuses" },
                  selectionSet: {
                    kind: "SelectionSet",
                    selections: [
                      {
                        kind: "InlineFragment",
                        typeCondition: {
                          kind: "NamedType",
                          name: {
                            kind: "Name",
                            value: "TimePartitionStatuses",
                          },
                        },
                        selectionSet: {
                          kind: "SelectionSet",
                          selections: [
                            {
                              kind: "Field",
                              name: { kind: "Name", value: "__typename" },
                            },
                            {
                              kind: "Field",
                              name: { kind: "Name", value: "ranges" },
                              selectionSet: {
                                kind: "SelectionSet",
                                selections: [
                                  {
                                    kind: "Field",
                                    name: { kind: "Name", value: "endKey" },
                                  },
                                  {
                                    kind: "Field",
                                    name: { kind: "Name", value: "startKey" },
                                  },
                                  {
                                    kind: "Field",
                                    name: { kind: "Name", value: "status" },
                                  },
                                ],
                              },
                            },
                          ],
                        },
                      },
                    ],
                  },
                },
                {
                  kind: "Field",
                  name: { kind: "Name", value: "assetMaterializations" },
                  arguments: [
                    {
                      kind: "Argument",
                      name: { kind: "Name", value: "limit" },
                      value: { kind: "IntValue", value: "1" },
                    },
                  ],
                  selectionSet: {
                    kind: "SelectionSet",
                    selections: [
                      {
                        kind: "Field",
                        name: { kind: "Name", value: "runOrError" },
                        selectionSet: {
                          kind: "SelectionSet",
                          selections: [
                            {
                              kind: "InlineFragment",
                              typeCondition: {
                                kind: "NamedType",
                                name: { kind: "Name", value: "Run" },
                              },
                              selectionSet: {
                                kind: "SelectionSet",
                                selections: [
                                  {
                                    kind: "Field",
                                    name: { kind: "Name", value: "endTime" },
                                  },
                                ],
                              },
                            },
                          ],
                        },
                      },
                    ],
                  },
                },
              ],
            },
          },
        ],
      },
    },
  ],
} as unknown as DocumentNode<
  AssetMaterializedDataQuery,
  AssetMaterializedDataQueryVariables
>;
export const TimeseriesMetricsByArtifactDocument = {
  kind: "Document",
  definitions: [
    {
      kind: "OperationDefinition",
      operation: "query",
      name: { kind: "Name", value: "TimeseriesMetricsByArtifact" },
      variableDefinitions: [
        {
          kind: "VariableDefinition",
          variable: {
            kind: "Variable",
            name: { kind: "Name", value: "artifactIds" },
          },
          type: {
            kind: "ListType",
            type: {
              kind: "NonNullType",
              type: {
                kind: "NamedType",
                name: { kind: "Name", value: "String" },
              },
            },
          },
        },
        {
          kind: "VariableDefinition",
          variable: {
            kind: "Variable",
            name: { kind: "Name", value: "metricIds" },
          },
          type: {
            kind: "ListType",
            type: {
              kind: "NonNullType",
              type: {
                kind: "NamedType",
                name: { kind: "Name", value: "String" },
              },
            },
          },
        },
        {
          kind: "VariableDefinition",
          variable: {
            kind: "Variable",
            name: { kind: "Name", value: "startDate" },
          },
          type: {
            kind: "NonNullType",
            type: {
              kind: "NamedType",
              name: { kind: "Name", value: "Oso_Date" },
            },
          },
        },
        {
          kind: "VariableDefinition",
          variable: {
            kind: "Variable",
            name: { kind: "Name", value: "endDate" },
          },
          type: {
            kind: "NonNullType",
            type: {
              kind: "NamedType",
              name: { kind: "Name", value: "Oso_Date" },
            },
          },
        },
      ],
      selectionSet: {
        kind: "SelectionSet",
        selections: [
          {
            kind: "Field",
            name: { kind: "Name", value: "oso_timeseriesMetricsByArtifactV0" },
            arguments: [
              {
                kind: "Argument",
                name: { kind: "Name", value: "where" },
                value: {
                  kind: "ObjectValue",
                  fields: [
                    {
                      kind: "ObjectField",
                      name: { kind: "Name", value: "artifactId" },
                      value: {
                        kind: "ObjectValue",
                        fields: [
                          {
                            kind: "ObjectField",
                            name: { kind: "Name", value: "_in" },
                            value: {
                              kind: "Variable",
                              name: { kind: "Name", value: "artifactIds" },
                            },
                          },
                        ],
                      },
                    },
                    {
                      kind: "ObjectField",
                      name: { kind: "Name", value: "metricId" },
                      value: {
                        kind: "ObjectValue",
                        fields: [
                          {
                            kind: "ObjectField",
                            name: { kind: "Name", value: "_in" },
                            value: {
                              kind: "Variable",
                              name: { kind: "Name", value: "metricIds" },
                            },
                          },
                        ],
                      },
                    },
                    {
                      kind: "ObjectField",
                      name: { kind: "Name", value: "sampleDate" },
                      value: {
                        kind: "ObjectValue",
                        fields: [
                          {
                            kind: "ObjectField",
                            name: { kind: "Name", value: "_gte" },
                            value: {
                              kind: "Variable",
                              name: { kind: "Name", value: "startDate" },
                            },
                          },
                          {
                            kind: "ObjectField",
                            name: { kind: "Name", value: "_lte" },
                            value: {
                              kind: "Variable",
                              name: { kind: "Name", value: "endDate" },
                            },
                          },
                        ],
                      },
                    },
                  ],
                },
              },
            ],
            selectionSet: {
              kind: "SelectionSet",
              selections: [
                { kind: "Field", name: { kind: "Name", value: "amount" } },
                { kind: "Field", name: { kind: "Name", value: "artifactId" } },
                { kind: "Field", name: { kind: "Name", value: "metricId" } },
                { kind: "Field", name: { kind: "Name", value: "sampleDate" } },
                { kind: "Field", name: { kind: "Name", value: "unit" } },
              ],
            },
          },
          {
            kind: "Field",
            name: { kind: "Name", value: "oso_artifactsV1" },
            arguments: [
              {
                kind: "Argument",
                name: { kind: "Name", value: "where" },
                value: {
                  kind: "ObjectValue",
                  fields: [
                    {
                      kind: "ObjectField",
                      name: { kind: "Name", value: "artifactId" },
                      value: {
                        kind: "ObjectValue",
                        fields: [
                          {
                            kind: "ObjectField",
                            name: { kind: "Name", value: "_in" },
                            value: {
                              kind: "Variable",
                              name: { kind: "Name", value: "artifactIds" },
                            },
                          },
                        ],
                      },
                    },
                  ],
                },
              },
            ],
            selectionSet: {
              kind: "SelectionSet",
              selections: [
                { kind: "Field", name: { kind: "Name", value: "artifactId" } },
                {
                  kind: "Field",
                  name: { kind: "Name", value: "artifactSource" },
                },
                {
                  kind: "Field",
                  name: { kind: "Name", value: "artifactNamespace" },
                },
                {
                  kind: "Field",
                  name: { kind: "Name", value: "artifactName" },
                },
              ],
            },
          },
          {
            kind: "Field",
            name: { kind: "Name", value: "oso_metricsV0" },
            arguments: [
              {
                kind: "Argument",
                name: { kind: "Name", value: "where" },
                value: {
                  kind: "ObjectValue",
                  fields: [
                    {
                      kind: "ObjectField",
                      name: { kind: "Name", value: "metricId" },
                      value: {
                        kind: "ObjectValue",
                        fields: [
                          {
                            kind: "ObjectField",
                            name: { kind: "Name", value: "_in" },
                            value: {
                              kind: "Variable",
                              name: { kind: "Name", value: "metricIds" },
                            },
                          },
                        ],
                      },
                    },
                  ],
                },
              },
            ],
            selectionSet: {
              kind: "SelectionSet",
              selections: [
                { kind: "Field", name: { kind: "Name", value: "metricId" } },
                {
                  kind: "Field",
                  name: { kind: "Name", value: "metricSource" },
                },
                {
                  kind: "Field",
                  name: { kind: "Name", value: "metricNamespace" },
                },
                { kind: "Field", name: { kind: "Name", value: "metricName" } },
                { kind: "Field", name: { kind: "Name", value: "displayName" } },
                { kind: "Field", name: { kind: "Name", value: "description" } },
              ],
            },
          },
        ],
      },
    },
  ],
} as unknown as DocumentNode<
  TimeseriesMetricsByArtifactQuery,
  TimeseriesMetricsByArtifactQueryVariables
>;
export const TimeseriesMetricsByProjectDocument = {
  kind: "Document",
  definitions: [
    {
      kind: "OperationDefinition",
      operation: "query",
      name: { kind: "Name", value: "TimeseriesMetricsByProject" },
      variableDefinitions: [
        {
          kind: "VariableDefinition",
          variable: {
            kind: "Variable",
            name: { kind: "Name", value: "projectIds" },
          },
          type: {
            kind: "ListType",
            type: {
              kind: "NonNullType",
              type: {
                kind: "NamedType",
                name: { kind: "Name", value: "String" },
              },
            },
          },
        },
        {
          kind: "VariableDefinition",
          variable: {
            kind: "Variable",
            name: { kind: "Name", value: "metricIds" },
          },
          type: {
            kind: "ListType",
            type: {
              kind: "NonNullType",
              type: {
                kind: "NamedType",
                name: { kind: "Name", value: "String" },
              },
            },
          },
        },
        {
          kind: "VariableDefinition",
          variable: {
            kind: "Variable",
            name: { kind: "Name", value: "startDate" },
          },
          type: {
            kind: "NonNullType",
            type: {
              kind: "NamedType",
              name: { kind: "Name", value: "Oso_Date" },
            },
          },
        },
        {
          kind: "VariableDefinition",
          variable: {
            kind: "Variable",
            name: { kind: "Name", value: "endDate" },
          },
          type: {
            kind: "NonNullType",
            type: {
              kind: "NamedType",
              name: { kind: "Name", value: "Oso_Date" },
            },
          },
        },
      ],
      selectionSet: {
        kind: "SelectionSet",
        selections: [
          {
            kind: "Field",
            name: { kind: "Name", value: "oso_timeseriesMetricsByProjectV0" },
            arguments: [
              {
                kind: "Argument",
                name: { kind: "Name", value: "where" },
                value: {
                  kind: "ObjectValue",
                  fields: [
                    {
                      kind: "ObjectField",
                      name: { kind: "Name", value: "projectId" },
                      value: {
                        kind: "ObjectValue",
                        fields: [
                          {
                            kind: "ObjectField",
                            name: { kind: "Name", value: "_in" },
                            value: {
                              kind: "Variable",
                              name: { kind: "Name", value: "projectIds" },
                            },
                          },
                        ],
                      },
                    },
                    {
                      kind: "ObjectField",
                      name: { kind: "Name", value: "metricId" },
                      value: {
                        kind: "ObjectValue",
                        fields: [
                          {
                            kind: "ObjectField",
                            name: { kind: "Name", value: "_in" },
                            value: {
                              kind: "Variable",
                              name: { kind: "Name", value: "metricIds" },
                            },
                          },
                        ],
                      },
                    },
                    {
                      kind: "ObjectField",
                      name: { kind: "Name", value: "sampleDate" },
                      value: {
                        kind: "ObjectValue",
                        fields: [
                          {
                            kind: "ObjectField",
                            name: { kind: "Name", value: "_gte" },
                            value: {
                              kind: "Variable",
                              name: { kind: "Name", value: "startDate" },
                            },
                          },
                          {
                            kind: "ObjectField",
                            name: { kind: "Name", value: "_lte" },
                            value: {
                              kind: "Variable",
                              name: { kind: "Name", value: "endDate" },
                            },
                          },
                        ],
                      },
                    },
                  ],
                },
              },
            ],
            selectionSet: {
              kind: "SelectionSet",
              selections: [
                { kind: "Field", name: { kind: "Name", value: "amount" } },
                { kind: "Field", name: { kind: "Name", value: "metricId" } },
                { kind: "Field", name: { kind: "Name", value: "projectId" } },
                { kind: "Field", name: { kind: "Name", value: "sampleDate" } },
                { kind: "Field", name: { kind: "Name", value: "unit" } },
              ],
            },
          },
          {
            kind: "Field",
            name: { kind: "Name", value: "oso_projectsV1" },
            arguments: [
              {
                kind: "Argument",
                name: { kind: "Name", value: "where" },
                value: {
                  kind: "ObjectValue",
                  fields: [
                    {
                      kind: "ObjectField",
                      name: { kind: "Name", value: "projectId" },
                      value: {
                        kind: "ObjectValue",
                        fields: [
                          {
                            kind: "ObjectField",
                            name: { kind: "Name", value: "_in" },
                            value: {
                              kind: "Variable",
                              name: { kind: "Name", value: "projectIds" },
                            },
                          },
                        ],
                      },
                    },
                  ],
                },
              },
            ],
            selectionSet: {
              kind: "SelectionSet",
              selections: [
                { kind: "Field", name: { kind: "Name", value: "projectId" } },
                {
                  kind: "Field",
                  name: { kind: "Name", value: "projectSource" },
                },
                {
                  kind: "Field",
                  name: { kind: "Name", value: "projectNamespace" },
                },
                { kind: "Field", name: { kind: "Name", value: "projectName" } },
                { kind: "Field", name: { kind: "Name", value: "displayName" } },
                { kind: "Field", name: { kind: "Name", value: "description" } },
              ],
            },
          },
          {
            kind: "Field",
            name: { kind: "Name", value: "oso_metricsV0" },
            arguments: [
              {
                kind: "Argument",
                name: { kind: "Name", value: "where" },
                value: {
                  kind: "ObjectValue",
                  fields: [
                    {
                      kind: "ObjectField",
                      name: { kind: "Name", value: "metricId" },
                      value: {
                        kind: "ObjectValue",
                        fields: [
                          {
                            kind: "ObjectField",
                            name: { kind: "Name", value: "_in" },
                            value: {
                              kind: "Variable",
                              name: { kind: "Name", value: "metricIds" },
                            },
                          },
                        ],
                      },
                    },
                  ],
                },
              },
            ],
            selectionSet: {
              kind: "SelectionSet",
              selections: [
                { kind: "Field", name: { kind: "Name", value: "metricId" } },
                {
                  kind: "Field",
                  name: { kind: "Name", value: "metricSource" },
                },
                {
                  kind: "Field",
                  name: { kind: "Name", value: "metricNamespace" },
                },
                { kind: "Field", name: { kind: "Name", value: "metricName" } },
                { kind: "Field", name: { kind: "Name", value: "displayName" } },
                { kind: "Field", name: { kind: "Name", value: "description" } },
              ],
            },
          },
        ],
      },
    },
  ],
} as unknown as DocumentNode<
  TimeseriesMetricsByProjectQuery,
  TimeseriesMetricsByProjectQueryVariables
>;
export const TimeseriesMetricsByCollectionDocument = {
  kind: "Document",
  definitions: [
    {
      kind: "OperationDefinition",
      operation: "query",
      name: { kind: "Name", value: "TimeseriesMetricsByCollection" },
      variableDefinitions: [
        {
          kind: "VariableDefinition",
          variable: {
            kind: "Variable",
            name: { kind: "Name", value: "collectionIds" },
          },
          type: {
            kind: "ListType",
            type: {
              kind: "NonNullType",
              type: {
                kind: "NamedType",
                name: { kind: "Name", value: "String" },
              },
            },
          },
        },
        {
          kind: "VariableDefinition",
          variable: {
            kind: "Variable",
            name: { kind: "Name", value: "metricIds" },
          },
          type: {
            kind: "ListType",
            type: {
              kind: "NonNullType",
              type: {
                kind: "NamedType",
                name: { kind: "Name", value: "String" },
              },
            },
          },
        },
        {
          kind: "VariableDefinition",
          variable: {
            kind: "Variable",
            name: { kind: "Name", value: "startDate" },
          },
          type: {
            kind: "NonNullType",
            type: {
              kind: "NamedType",
              name: { kind: "Name", value: "Oso_Date" },
            },
          },
        },
        {
          kind: "VariableDefinition",
          variable: {
            kind: "Variable",
            name: { kind: "Name", value: "endDate" },
          },
          type: {
            kind: "NonNullType",
            type: {
              kind: "NamedType",
              name: { kind: "Name", value: "Oso_Date" },
            },
          },
        },
      ],
      selectionSet: {
        kind: "SelectionSet",
        selections: [
          {
            kind: "Field",
            name: {
              kind: "Name",
              value: "oso_timeseriesMetricsByCollectionV0",
            },
            arguments: [
              {
                kind: "Argument",
                name: { kind: "Name", value: "where" },
                value: {
                  kind: "ObjectValue",
                  fields: [
                    {
                      kind: "ObjectField",
                      name: { kind: "Name", value: "collectionId" },
                      value: {
                        kind: "ObjectValue",
                        fields: [
                          {
                            kind: "ObjectField",
                            name: { kind: "Name", value: "_in" },
                            value: {
                              kind: "Variable",
                              name: { kind: "Name", value: "collectionIds" },
                            },
                          },
                        ],
                      },
                    },
                    {
                      kind: "ObjectField",
                      name: { kind: "Name", value: "metricId" },
                      value: {
                        kind: "ObjectValue",
                        fields: [
                          {
                            kind: "ObjectField",
                            name: { kind: "Name", value: "_in" },
                            value: {
                              kind: "Variable",
                              name: { kind: "Name", value: "metricIds" },
                            },
                          },
                        ],
                      },
                    },
                    {
                      kind: "ObjectField",
                      name: { kind: "Name", value: "sampleDate" },
                      value: {
                        kind: "ObjectValue",
                        fields: [
                          {
                            kind: "ObjectField",
                            name: { kind: "Name", value: "_gte" },
                            value: {
                              kind: "Variable",
                              name: { kind: "Name", value: "startDate" },
                            },
                          },
                          {
                            kind: "ObjectField",
                            name: { kind: "Name", value: "_lte" },
                            value: {
                              kind: "Variable",
                              name: { kind: "Name", value: "endDate" },
                            },
                          },
                        ],
                      },
                    },
                  ],
                },
              },
            ],
            selectionSet: {
              kind: "SelectionSet",
              selections: [
                { kind: "Field", name: { kind: "Name", value: "amount" } },
                { kind: "Field", name: { kind: "Name", value: "metricId" } },
                {
                  kind: "Field",
                  name: { kind: "Name", value: "collectionId" },
                },
                { kind: "Field", name: { kind: "Name", value: "sampleDate" } },
                { kind: "Field", name: { kind: "Name", value: "unit" } },
              ],
            },
          },
          {
            kind: "Field",
            name: { kind: "Name", value: "oso_collectionsV1" },
            arguments: [
              {
                kind: "Argument",
                name: { kind: "Name", value: "where" },
                value: {
                  kind: "ObjectValue",
                  fields: [
                    {
                      kind: "ObjectField",
                      name: { kind: "Name", value: "collectionId" },
                      value: {
                        kind: "ObjectValue",
                        fields: [
                          {
                            kind: "ObjectField",
                            name: { kind: "Name", value: "_in" },
                            value: {
                              kind: "Variable",
                              name: { kind: "Name", value: "collectionIds" },
                            },
                          },
                        ],
                      },
                    },
                  ],
                },
              },
            ],
            selectionSet: {
              kind: "SelectionSet",
              selections: [
                {
                  kind: "Field",
                  name: { kind: "Name", value: "collectionId" },
                },
                {
                  kind: "Field",
                  name: { kind: "Name", value: "collectionSource" },
                },
                {
                  kind: "Field",
                  name: { kind: "Name", value: "collectionNamespace" },
                },
                {
                  kind: "Field",
                  name: { kind: "Name", value: "collectionName" },
                },
                { kind: "Field", name: { kind: "Name", value: "displayName" } },
                { kind: "Field", name: { kind: "Name", value: "description" } },
              ],
            },
          },
          {
            kind: "Field",
            name: { kind: "Name", value: "oso_metricsV0" },
            arguments: [
              {
                kind: "Argument",
                name: { kind: "Name", value: "where" },
                value: {
                  kind: "ObjectValue",
                  fields: [
                    {
                      kind: "ObjectField",
                      name: { kind: "Name", value: "metricId" },
                      value: {
                        kind: "ObjectValue",
                        fields: [
                          {
                            kind: "ObjectField",
                            name: { kind: "Name", value: "_in" },
                            value: {
                              kind: "Variable",
                              name: { kind: "Name", value: "metricIds" },
                            },
                          },
                        ],
                      },
                    },
                  ],
                },
              },
            ],
            selectionSet: {
              kind: "SelectionSet",
              selections: [
                { kind: "Field", name: { kind: "Name", value: "metricId" } },
                {
                  kind: "Field",
                  name: { kind: "Name", value: "metricSource" },
                },
                {
                  kind: "Field",
                  name: { kind: "Name", value: "metricNamespace" },
                },
                { kind: "Field", name: { kind: "Name", value: "metricName" } },
                { kind: "Field", name: { kind: "Name", value: "displayName" } },
                { kind: "Field", name: { kind: "Name", value: "description" } },
              ],
            },
          },
        ],
      },
    },
  ],
} as unknown as DocumentNode<
  TimeseriesMetricsByCollectionQuery,
  TimeseriesMetricsByCollectionQueryVariables
>;
