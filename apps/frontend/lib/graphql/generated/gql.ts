/* eslint-disable */
import * as types from "./graphql";
import { TypedDocumentNode as DocumentNode } from "@graphql-typed-document-node/core";

/**
 * Map of all GraphQL operations in the project.
 *
 * This map has several performance disadvantages:
 * 1. It is not tree-shakeable, so it will include all operations in the project.
 * 2. It is not minifiable, so the string of a GraphQL query will be multiple times inside the bundle.
 * 3. It does not support dead code elimination, so it will add unused operations.
 *
 * Therefore it is highly recommended to use the babel or swc plugin for production.
 * Learn more about it here: https://the-guild.dev/graphql/codegen/plugins/presets/preset-client#reducing-bundle-size
 */
type Documents = {
  "\n      mutation SavePreview($input: SaveNotebookPreviewInput!) {\n        saveNotebookPreview(input: $input) {\n          success\n          message\n        }\n      }\n    ": typeof types.SavePreviewDocument;
  "\n      mutation CreateDataset($input: CreateDatasetInput!) {\n        createDataset(input: $input) {\n          success\n          message\n          dataset {\n            id\n            name\n            displayName\n            description\n            type\n            isPublic\n          }\n        }\n      }\n    ": typeof types.CreateDatasetDocument;
  "\n      mutation UpdateDataset($input: UpdateDatasetInput!) {\n        updateDataset(input: $input) {\n          success\n          message\n          dataset {\n            id\n            name\n            displayName\n            description\n            isPublic\n          }\n        }\n      }\n    ": typeof types.UpdateDatasetDocument;
  "\n      mutation CreateDataModel($input: CreateDataModelInput!) {\n        createDataModel(input: $input) {\n          success\n          message\n          dataModel {\n            id\n            name\n            isEnabled\n          }\n        }\n      }\n    ": typeof types.CreateDataModelDocument;
  "\n      mutation UpdateDataModel($input: UpdateDataModelInput!) {\n        updateDataModel(input: $input) {\n          success\n          message\n          dataModel {\n            id\n            name\n            isEnabled\n          }\n        }\n      }\n    ": typeof types.UpdateDataModelDocument;
  "\n      mutation CreateDataModelRevision($input: CreateDataModelRevisionInput!) {\n        createDataModelRevision(input: $input) {\n          success\n          message\n          dataModelRevision {\n            id\n            revisionNumber\n          }\n        }\n      }\n    ": typeof types.CreateDataModelRevisionDocument;
  "\n      mutation CreateDataModelRelease($input: CreateDataModelReleaseInput!) {\n        createDataModelRelease(input: $input) {\n          success\n          message\n          dataModelRelease {\n            id\n          }\n        }\n      }\n    ": typeof types.CreateDataModelReleaseDocument;
  "\nquery AssetGraph {\n  assetNodes {\n    assetKey {\n      path\n    }\n    dependencyKeys {\n      path\n    }\n  }\n}": typeof types.AssetGraphDocument;
  '\nquery AssetMaterializedData($assetKeys: [AssetKeyInput!] = {path: ""}) {\n  assetNodes(assetKeys: $assetKeys) {\n    assetKey {\n      path\n    }\n    partitionStats {\n      numFailed\n      numMaterialized\n      numMaterializing\n      numPartitions\n    }\n    assetPartitionStatuses {\n      ... on TimePartitionStatuses {\n        __typename\n        ranges {\n          endKey\n          startKey\n          status\n        }\n      }\n    }\n    assetMaterializations(limit: 1) {\n      runOrError {\n        ... on Run {\n          endTime\n        }\n      }\n    }\n  }\n}': typeof types.AssetMaterializedDataDocument;
  "\n  query TimeseriesMetricsByArtifact(\n    $artifactIds: [String!],\n    $metricIds: [String!],\n    $startDate: Oso_Date!,\n    $endDate: Oso_Date!, \n  ) {\n    oso_timeseriesMetricsByArtifactV0(where: {\n      artifactId: {_in: $artifactIds},\n      metricId: {_in: $metricIds},\n      sampleDate: { _gte: $startDate, _lte: $endDate }\n    }) {\n      amount\n      artifactId\n      metricId\n      sampleDate\n      unit\n    }\n    oso_artifactsV1(where: { artifactId: { _in: $artifactIds }}) {\n      artifactId\n      artifactSource\n      artifactNamespace\n      artifactName\n    }\n    oso_metricsV0(where: {metricId: {_in: $metricIds}}) {\n      metricId\n      metricSource\n      metricNamespace\n      metricName\n      displayName\n      description\n    }\n  }\n": typeof types.TimeseriesMetricsByArtifactDocument;
  "\n  query TimeseriesMetricsByProject(\n    $projectIds: [String!],\n    $metricIds: [String!],\n    $startDate: Oso_Date!,\n    $endDate: Oso_Date!, \n  ) {\n    oso_timeseriesMetricsByProjectV0(where: {\n      projectId: {_in: $projectIds},\n      metricId: {_in: $metricIds},\n      sampleDate: { _gte: $startDate, _lte: $endDate }\n    }) {\n      amount\n      metricId\n      projectId\n      sampleDate\n      unit\n    }\n    oso_projectsV1(where: { projectId: { _in: $projectIds }}) {\n      projectId\n      projectSource\n      projectNamespace\n      projectName\n      displayName\n      description\n    }\n    oso_metricsV0(where: {metricId: {_in: $metricIds}}) {\n      metricId\n      metricSource\n      metricNamespace\n      metricName\n      displayName\n      description\n    }\n  }\n": typeof types.TimeseriesMetricsByProjectDocument;
  "\n  query TimeseriesMetricsByCollection(\n    $collectionIds: [String!],\n    $metricIds: [String!],\n    $startDate: Oso_Date!,\n    $endDate: Oso_Date!, \n  ) {\n    oso_timeseriesMetricsByCollectionV0(where: {\n      collectionId: {_in: $collectionIds},\n      metricId: {_in: $metricIds},\n      sampleDate: { _gte: $startDate, _lte: $endDate }\n    }) {\n      amount\n      metricId\n      collectionId\n      sampleDate\n      unit\n    }\n    oso_collectionsV1(where: { collectionId: { _in: $collectionIds }}) {\n      collectionId\n      collectionSource\n      collectionNamespace\n      collectionName\n      displayName\n      description\n    }\n    oso_metricsV0(where: {metricId: {_in: $metricIds}}) {\n      metricId\n      metricSource\n      metricNamespace\n      metricName\n      displayName\n      description\n    }\n  }\n": typeof types.TimeseriesMetricsByCollectionDocument;
};
const documents: Documents = {
  "\n      mutation SavePreview($input: SaveNotebookPreviewInput!) {\n        saveNotebookPreview(input: $input) {\n          success\n          message\n        }\n      }\n    ":
    types.SavePreviewDocument,
  "\n      mutation CreateDataset($input: CreateDatasetInput!) {\n        createDataset(input: $input) {\n          success\n          message\n          dataset {\n            id\n            name\n            displayName\n            description\n            type\n            isPublic\n          }\n        }\n      }\n    ":
    types.CreateDatasetDocument,
  "\n      mutation UpdateDataset($input: UpdateDatasetInput!) {\n        updateDataset(input: $input) {\n          success\n          message\n          dataset {\n            id\n            name\n            displayName\n            description\n            isPublic\n          }\n        }\n      }\n    ":
    types.UpdateDatasetDocument,
  "\n      mutation CreateDataModel($input: CreateDataModelInput!) {\n        createDataModel(input: $input) {\n          success\n          message\n          dataModel {\n            id\n            name\n            isEnabled\n          }\n        }\n      }\n    ":
    types.CreateDataModelDocument,
  "\n      mutation UpdateDataModel($input: UpdateDataModelInput!) {\n        updateDataModel(input: $input) {\n          success\n          message\n          dataModel {\n            id\n            name\n            isEnabled\n          }\n        }\n      }\n    ":
    types.UpdateDataModelDocument,
  "\n      mutation CreateDataModelRevision($input: CreateDataModelRevisionInput!) {\n        createDataModelRevision(input: $input) {\n          success\n          message\n          dataModelRevision {\n            id\n            revisionNumber\n          }\n        }\n      }\n    ":
    types.CreateDataModelRevisionDocument,
  "\n      mutation CreateDataModelRelease($input: CreateDataModelReleaseInput!) {\n        createDataModelRelease(input: $input) {\n          success\n          message\n          dataModelRelease {\n            id\n          }\n        }\n      }\n    ":
    types.CreateDataModelReleaseDocument,
  "\nquery AssetGraph {\n  assetNodes {\n    assetKey {\n      path\n    }\n    dependencyKeys {\n      path\n    }\n  }\n}":
    types.AssetGraphDocument,
  '\nquery AssetMaterializedData($assetKeys: [AssetKeyInput!] = {path: ""}) {\n  assetNodes(assetKeys: $assetKeys) {\n    assetKey {\n      path\n    }\n    partitionStats {\n      numFailed\n      numMaterialized\n      numMaterializing\n      numPartitions\n    }\n    assetPartitionStatuses {\n      ... on TimePartitionStatuses {\n        __typename\n        ranges {\n          endKey\n          startKey\n          status\n        }\n      }\n    }\n    assetMaterializations(limit: 1) {\n      runOrError {\n        ... on Run {\n          endTime\n        }\n      }\n    }\n  }\n}':
    types.AssetMaterializedDataDocument,
  "\n  query TimeseriesMetricsByArtifact(\n    $artifactIds: [String!],\n    $metricIds: [String!],\n    $startDate: Oso_Date!,\n    $endDate: Oso_Date!, \n  ) {\n    oso_timeseriesMetricsByArtifactV0(where: {\n      artifactId: {_in: $artifactIds},\n      metricId: {_in: $metricIds},\n      sampleDate: { _gte: $startDate, _lte: $endDate }\n    }) {\n      amount\n      artifactId\n      metricId\n      sampleDate\n      unit\n    }\n    oso_artifactsV1(where: { artifactId: { _in: $artifactIds }}) {\n      artifactId\n      artifactSource\n      artifactNamespace\n      artifactName\n    }\n    oso_metricsV0(where: {metricId: {_in: $metricIds}}) {\n      metricId\n      metricSource\n      metricNamespace\n      metricName\n      displayName\n      description\n    }\n  }\n":
    types.TimeseriesMetricsByArtifactDocument,
  "\n  query TimeseriesMetricsByProject(\n    $projectIds: [String!],\n    $metricIds: [String!],\n    $startDate: Oso_Date!,\n    $endDate: Oso_Date!, \n  ) {\n    oso_timeseriesMetricsByProjectV0(where: {\n      projectId: {_in: $projectIds},\n      metricId: {_in: $metricIds},\n      sampleDate: { _gte: $startDate, _lte: $endDate }\n    }) {\n      amount\n      metricId\n      projectId\n      sampleDate\n      unit\n    }\n    oso_projectsV1(where: { projectId: { _in: $projectIds }}) {\n      projectId\n      projectSource\n      projectNamespace\n      projectName\n      displayName\n      description\n    }\n    oso_metricsV0(where: {metricId: {_in: $metricIds}}) {\n      metricId\n      metricSource\n      metricNamespace\n      metricName\n      displayName\n      description\n    }\n  }\n":
    types.TimeseriesMetricsByProjectDocument,
  "\n  query TimeseriesMetricsByCollection(\n    $collectionIds: [String!],\n    $metricIds: [String!],\n    $startDate: Oso_Date!,\n    $endDate: Oso_Date!, \n  ) {\n    oso_timeseriesMetricsByCollectionV0(where: {\n      collectionId: {_in: $collectionIds},\n      metricId: {_in: $metricIds},\n      sampleDate: { _gte: $startDate, _lte: $endDate }\n    }) {\n      amount\n      metricId\n      collectionId\n      sampleDate\n      unit\n    }\n    oso_collectionsV1(where: { collectionId: { _in: $collectionIds }}) {\n      collectionId\n      collectionSource\n      collectionNamespace\n      collectionName\n      displayName\n      description\n    }\n    oso_metricsV0(where: {metricId: {_in: $metricIds}}) {\n      metricId\n      metricSource\n      metricNamespace\n      metricName\n      displayName\n      description\n    }\n  }\n":
    types.TimeseriesMetricsByCollectionDocument,
};

/**
 * The gql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 *
 *
 * @example
 * ```ts
 * const query = gql(`query GetUser($id: ID!) { user(id: $id) { name } }`);
 * ```
 *
 * The query argument is unknown!
 * Please regenerate the types.
 */
export function gql(source: string): unknown;

/**
 * The gql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function gql(
  source: "\n      mutation SavePreview($input: SaveNotebookPreviewInput!) {\n        saveNotebookPreview(input: $input) {\n          success\n          message\n        }\n      }\n    ",
): (typeof documents)["\n      mutation SavePreview($input: SaveNotebookPreviewInput!) {\n        saveNotebookPreview(input: $input) {\n          success\n          message\n        }\n      }\n    "];
/**
 * The gql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function gql(
  source: "\n      mutation CreateDataset($input: CreateDatasetInput!) {\n        createDataset(input: $input) {\n          success\n          message\n          dataset {\n            id\n            name\n            displayName\n            description\n            type\n            isPublic\n          }\n        }\n      }\n    ",
): (typeof documents)["\n      mutation CreateDataset($input: CreateDatasetInput!) {\n        createDataset(input: $input) {\n          success\n          message\n          dataset {\n            id\n            name\n            displayName\n            description\n            type\n            isPublic\n          }\n        }\n      }\n    "];
/**
 * The gql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function gql(
  source: "\n      mutation UpdateDataset($input: UpdateDatasetInput!) {\n        updateDataset(input: $input) {\n          success\n          message\n          dataset {\n            id\n            name\n            displayName\n            description\n            isPublic\n          }\n        }\n      }\n    ",
): (typeof documents)["\n      mutation UpdateDataset($input: UpdateDatasetInput!) {\n        updateDataset(input: $input) {\n          success\n          message\n          dataset {\n            id\n            name\n            displayName\n            description\n            isPublic\n          }\n        }\n      }\n    "];
/**
 * The gql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function gql(
  source: "\n      mutation CreateDataModel($input: CreateDataModelInput!) {\n        createDataModel(input: $input) {\n          success\n          message\n          dataModel {\n            id\n            name\n            isEnabled\n          }\n        }\n      }\n    ",
): (typeof documents)["\n      mutation CreateDataModel($input: CreateDataModelInput!) {\n        createDataModel(input: $input) {\n          success\n          message\n          dataModel {\n            id\n            name\n            isEnabled\n          }\n        }\n      }\n    "];
/**
 * The gql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function gql(
  source: "\n      mutation UpdateDataModel($input: UpdateDataModelInput!) {\n        updateDataModel(input: $input) {\n          success\n          message\n          dataModel {\n            id\n            name\n            isEnabled\n          }\n        }\n      }\n    ",
): (typeof documents)["\n      mutation UpdateDataModel($input: UpdateDataModelInput!) {\n        updateDataModel(input: $input) {\n          success\n          message\n          dataModel {\n            id\n            name\n            isEnabled\n          }\n        }\n      }\n    "];
/**
 * The gql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function gql(
  source: "\n      mutation CreateDataModelRevision($input: CreateDataModelRevisionInput!) {\n        createDataModelRevision(input: $input) {\n          success\n          message\n          dataModelRevision {\n            id\n            revisionNumber\n          }\n        }\n      }\n    ",
): (typeof documents)["\n      mutation CreateDataModelRevision($input: CreateDataModelRevisionInput!) {\n        createDataModelRevision(input: $input) {\n          success\n          message\n          dataModelRevision {\n            id\n            revisionNumber\n          }\n        }\n      }\n    "];
/**
 * The gql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function gql(
  source: "\n      mutation CreateDataModelRelease($input: CreateDataModelReleaseInput!) {\n        createDataModelRelease(input: $input) {\n          success\n          message\n          dataModelRelease {\n            id\n          }\n        }\n      }\n    ",
): (typeof documents)["\n      mutation CreateDataModelRelease($input: CreateDataModelReleaseInput!) {\n        createDataModelRelease(input: $input) {\n          success\n          message\n          dataModelRelease {\n            id\n          }\n        }\n      }\n    "];
/**
 * The gql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function gql(
  source: "\nquery AssetGraph {\n  assetNodes {\n    assetKey {\n      path\n    }\n    dependencyKeys {\n      path\n    }\n  }\n}",
): (typeof documents)["\nquery AssetGraph {\n  assetNodes {\n    assetKey {\n      path\n    }\n    dependencyKeys {\n      path\n    }\n  }\n}"];
/**
 * The gql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function gql(
  source: '\nquery AssetMaterializedData($assetKeys: [AssetKeyInput!] = {path: ""}) {\n  assetNodes(assetKeys: $assetKeys) {\n    assetKey {\n      path\n    }\n    partitionStats {\n      numFailed\n      numMaterialized\n      numMaterializing\n      numPartitions\n    }\n    assetPartitionStatuses {\n      ... on TimePartitionStatuses {\n        __typename\n        ranges {\n          endKey\n          startKey\n          status\n        }\n      }\n    }\n    assetMaterializations(limit: 1) {\n      runOrError {\n        ... on Run {\n          endTime\n        }\n      }\n    }\n  }\n}',
): (typeof documents)['\nquery AssetMaterializedData($assetKeys: [AssetKeyInput!] = {path: ""}) {\n  assetNodes(assetKeys: $assetKeys) {\n    assetKey {\n      path\n    }\n    partitionStats {\n      numFailed\n      numMaterialized\n      numMaterializing\n      numPartitions\n    }\n    assetPartitionStatuses {\n      ... on TimePartitionStatuses {\n        __typename\n        ranges {\n          endKey\n          startKey\n          status\n        }\n      }\n    }\n    assetMaterializations(limit: 1) {\n      runOrError {\n        ... on Run {\n          endTime\n        }\n      }\n    }\n  }\n}'];
/**
 * The gql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function gql(
  source: "\n  query TimeseriesMetricsByArtifact(\n    $artifactIds: [String!],\n    $metricIds: [String!],\n    $startDate: Oso_Date!,\n    $endDate: Oso_Date!, \n  ) {\n    oso_timeseriesMetricsByArtifactV0(where: {\n      artifactId: {_in: $artifactIds},\n      metricId: {_in: $metricIds},\n      sampleDate: { _gte: $startDate, _lte: $endDate }\n    }) {\n      amount\n      artifactId\n      metricId\n      sampleDate\n      unit\n    }\n    oso_artifactsV1(where: { artifactId: { _in: $artifactIds }}) {\n      artifactId\n      artifactSource\n      artifactNamespace\n      artifactName\n    }\n    oso_metricsV0(where: {metricId: {_in: $metricIds}}) {\n      metricId\n      metricSource\n      metricNamespace\n      metricName\n      displayName\n      description\n    }\n  }\n",
): (typeof documents)["\n  query TimeseriesMetricsByArtifact(\n    $artifactIds: [String!],\n    $metricIds: [String!],\n    $startDate: Oso_Date!,\n    $endDate: Oso_Date!, \n  ) {\n    oso_timeseriesMetricsByArtifactV0(where: {\n      artifactId: {_in: $artifactIds},\n      metricId: {_in: $metricIds},\n      sampleDate: { _gte: $startDate, _lte: $endDate }\n    }) {\n      amount\n      artifactId\n      metricId\n      sampleDate\n      unit\n    }\n    oso_artifactsV1(where: { artifactId: { _in: $artifactIds }}) {\n      artifactId\n      artifactSource\n      artifactNamespace\n      artifactName\n    }\n    oso_metricsV0(where: {metricId: {_in: $metricIds}}) {\n      metricId\n      metricSource\n      metricNamespace\n      metricName\n      displayName\n      description\n    }\n  }\n"];
/**
 * The gql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function gql(
  source: "\n  query TimeseriesMetricsByProject(\n    $projectIds: [String!],\n    $metricIds: [String!],\n    $startDate: Oso_Date!,\n    $endDate: Oso_Date!, \n  ) {\n    oso_timeseriesMetricsByProjectV0(where: {\n      projectId: {_in: $projectIds},\n      metricId: {_in: $metricIds},\n      sampleDate: { _gte: $startDate, _lte: $endDate }\n    }) {\n      amount\n      metricId\n      projectId\n      sampleDate\n      unit\n    }\n    oso_projectsV1(where: { projectId: { _in: $projectIds }}) {\n      projectId\n      projectSource\n      projectNamespace\n      projectName\n      displayName\n      description\n    }\n    oso_metricsV0(where: {metricId: {_in: $metricIds}}) {\n      metricId\n      metricSource\n      metricNamespace\n      metricName\n      displayName\n      description\n    }\n  }\n",
): (typeof documents)["\n  query TimeseriesMetricsByProject(\n    $projectIds: [String!],\n    $metricIds: [String!],\n    $startDate: Oso_Date!,\n    $endDate: Oso_Date!, \n  ) {\n    oso_timeseriesMetricsByProjectV0(where: {\n      projectId: {_in: $projectIds},\n      metricId: {_in: $metricIds},\n      sampleDate: { _gte: $startDate, _lte: $endDate }\n    }) {\n      amount\n      metricId\n      projectId\n      sampleDate\n      unit\n    }\n    oso_projectsV1(where: { projectId: { _in: $projectIds }}) {\n      projectId\n      projectSource\n      projectNamespace\n      projectName\n      displayName\n      description\n    }\n    oso_metricsV0(where: {metricId: {_in: $metricIds}}) {\n      metricId\n      metricSource\n      metricNamespace\n      metricName\n      displayName\n      description\n    }\n  }\n"];
/**
 * The gql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function gql(
  source: "\n  query TimeseriesMetricsByCollection(\n    $collectionIds: [String!],\n    $metricIds: [String!],\n    $startDate: Oso_Date!,\n    $endDate: Oso_Date!, \n  ) {\n    oso_timeseriesMetricsByCollectionV0(where: {\n      collectionId: {_in: $collectionIds},\n      metricId: {_in: $metricIds},\n      sampleDate: { _gte: $startDate, _lte: $endDate }\n    }) {\n      amount\n      metricId\n      collectionId\n      sampleDate\n      unit\n    }\n    oso_collectionsV1(where: { collectionId: { _in: $collectionIds }}) {\n      collectionId\n      collectionSource\n      collectionNamespace\n      collectionName\n      displayName\n      description\n    }\n    oso_metricsV0(where: {metricId: {_in: $metricIds}}) {\n      metricId\n      metricSource\n      metricNamespace\n      metricName\n      displayName\n      description\n    }\n  }\n",
): (typeof documents)["\n  query TimeseriesMetricsByCollection(\n    $collectionIds: [String!],\n    $metricIds: [String!],\n    $startDate: Oso_Date!,\n    $endDate: Oso_Date!, \n  ) {\n    oso_timeseriesMetricsByCollectionV0(where: {\n      collectionId: {_in: $collectionIds},\n      metricId: {_in: $metricIds},\n      sampleDate: { _gte: $startDate, _lte: $endDate }\n    }) {\n      amount\n      metricId\n      collectionId\n      sampleDate\n      unit\n    }\n    oso_collectionsV1(where: { collectionId: { _in: $collectionIds }}) {\n      collectionId\n      collectionSource\n      collectionNamespace\n      collectionName\n      displayName\n      description\n    }\n    oso_metricsV0(where: {metricId: {_in: $metricIds}}) {\n      metricId\n      metricSource\n      metricNamespace\n      metricName\n      displayName\n      description\n    }\n  }\n"];

export function gql(source: string) {
  return (documents as any)[source] ?? {};
}

export type DocumentType<TDocumentNode extends DocumentNode<any, any>> =
  TDocumentNode extends DocumentNode<infer TType, any> ? TType : never;
