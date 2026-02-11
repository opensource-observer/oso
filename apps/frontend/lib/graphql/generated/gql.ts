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
  "\n  query GetPreviewData($datasetId: ID!, $tableName: String!) {\n    datasets(where: { id: { eq: $datasetId } }, single: true) {\n      edges {\n        node {\n          id\n          typeDefinition {\n            __typename\n            ... on DataModelDefinition {\n              dataModels(where: { name: { eq: $tableName } }, single: true) {\n                edges {\n                  node {\n                    id\n                    name\n                    previewData {\n                        isAvailable\n                        rows\n                    }\n                  }\n                }\n              }\n            }\n            ... on StaticModelDefinition {\n              staticModels(where: { name: { eq: $tableName } }, single: true) {\n                edges {\n                  node {\n                    id\n                    name\n                    previewData {\n                      isAvailable\n                      rows\n                    }\n                  }\n                }\n              }\n            }\n            ... on DataIngestionDefinition {\n              dataIngestion {\n                id\n                previewData(tableName: $tableName) {\n                  isAvailable\n                  rows\n                }\n              }\n            }\n            ... on DataConnectionDefinition {\n              dataConnectionAlias {\n                id\n                schema\n                previewData(tableName: $tableName) {\n                  isAvailable\n                  rows\n                }\n              }\n            }\n          }\n        }\n      }\n    }\n  }\n": typeof types.GetPreviewDataDocument;
  "\n      mutation PublishNotebook($notebookId: ID!) {\n        publishNotebook(notebookId: $notebookId) {\n          success\n          message\n          run {\n            id\n          }\n        }\n      }\n    ": typeof types.PublishNotebookDocument;
  "\n      mutation UnpublishNotebook($notebookId: ID!) {\n        unpublishNotebook(notebookId: $notebookId) {\n          success\n          message\n        }\n      }\n    ": typeof types.UnpublishNotebookDocument;
  "\n      mutation CreateDataConnection($input: CreateDataConnectionInput!) {\n        createDataConnection(input: $input) {\n          success\n          message\n          dataConnection {\n            id\n            orgId\n            name\n            type\n            config\n          }\n        }\n      }\n    ": typeof types.CreateDataConnectionDocument;
  "\n      mutation DeleteDataConnection($id: ID!) {\n        deleteDataConnection(id: $id) {\n          success\n          message\n        }\n      }\n    ": typeof types.DeleteDataConnectionDocument;
  "\n      mutation SyncDataConnection($id: ID!) {\n        syncDataConnection(id: $id) {\n          success\n          message\n          run {\n            id\n          }\n        }\n      }\n    ": typeof types.SyncDataConnectionDocument;
  "\n      mutation SavePreview($input: SaveNotebookPreviewInput!) {\n        saveNotebookPreview(input: $input) {\n          success\n          message\n        }\n      }\n    ": typeof types.SavePreviewDocument;
  "\n      mutation CreateDataset($input: CreateDatasetInput!) {\n        createDataset(input: $input) {\n          success\n          message\n          dataset {\n            id\n            name\n            displayName\n            description\n            type\n          }\n        }\n      }\n    ": typeof types.CreateDatasetDocument;
  "\n      mutation UpdateDataset($input: UpdateDatasetInput!) {\n        updateDataset(input: $input) {\n          success\n          message\n          dataset {\n            id\n            name\n            displayName\n            description\n          }\n        }\n      }\n    ": typeof types.UpdateDatasetDocument;
  "\n      mutation DeleteDataset($id: ID!) {\n        deleteDataset(id: $id) {\n          success\n          message\n        }\n      }\n    ": typeof types.DeleteDatasetDocument;
  "\n      mutation CreateDataModel($input: CreateDataModelInput!) {\n        createDataModel(input: $input) {\n          success\n          message\n          dataModel {\n            id\n            name\n            isEnabled\n          }\n        }\n      }\n    ": typeof types.CreateDataModelDocument;
  "\n      mutation UpdateDataModel($input: UpdateDataModelInput!) {\n        updateDataModel(input: $input) {\n          success\n          message\n          dataModel {\n            id\n            name\n            isEnabled\n          }\n        }\n      }\n    ": typeof types.UpdateDataModelDocument;
  "\n      mutation DeleteDataModel($id: ID!) {\n        deleteDataModel(id: $id) {\n          success\n          message\n        }\n      }\n    ": typeof types.DeleteDataModelDocument;
  "\n      mutation CreateDataModelRevision($input: CreateDataModelRevisionInput!) {\n        createDataModelRevision(input: $input) {\n          success\n          message\n          dataModelRevision {\n            id\n            createdAt\n            revisionNumber\n          }\n        }\n      }\n    ": typeof types.CreateDataModelRevisionDocument;
  "\n      mutation CreateDataModelRelease($input: CreateDataModelReleaseInput!) {\n        createDataModelRelease(input: $input) {\n          success\n          message\n          dataModelRelease {\n            id\n          }\n        }\n      }\n    ": typeof types.CreateDataModelReleaseDocument;
  "\n      mutation UpdateModelContext($input: UpdateModelContextInput!) {\n        updateModelContext(input: $input) {\n          success\n          message\n          modelContext {\n            id\n            context\n            columnContext {\n              name\n              context\n            }\n          }\n        }\n      }\n    ": typeof types.UpdateModelContextDocument;
  "\n      mutation CreateStaticModel($input: CreateStaticModelInput!) {\n        createStaticModel(input: $input) {\n          success\n          message\n          staticModel {\n            id\n            name\n          }\n        }\n      }\n    ": typeof types.CreateStaticModelDocument;
  "\n      mutation UpdateStaticModel($input: UpdateStaticModelInput!) {\n        updateStaticModel(input: $input) {\n          success\n          message\n          staticModel {\n            id\n            name\n          }\n        }\n      }\n    ": typeof types.UpdateStaticModelDocument;
  "\n      mutation DeleteStaticModel($id: ID!) {\n        deleteStaticModel(id: $id) {\n          success\n          message\n        }\n      }\n    ": typeof types.DeleteStaticModelDocument;
  "\n      mutation CreateUserModelRunRequest($input: CreateUserModelRunRequestInput!) {\n        createUserModelRunRequest(input: $input) {\n          success\n          message\n          run {\n            id\n          }\n        }\n      }\n    ": typeof types.CreateUserModelRunRequestDocument;
  "\n      mutation CreateStaticModelRunRequest($input: CreateStaticModelRunRequestInput!) {\n        createStaticModelRunRequest(input: $input) {\n          success\n          message\n          run {\n            id\n          }\n        }\n      }\n    ": typeof types.CreateStaticModelRunRequestDocument;
  "\n      mutation CreateDataIngestionConfig($input: CreateDataIngestionInput!) {\n        createDataIngestionConfig(input: $input) {\n          id\n          datasetId\n          factoryType\n          config\n          createdAt\n          updatedAt\n        }\n      }\n    ": typeof types.CreateDataIngestionConfigDocument;
  "\n      mutation CreateDataIngestionRunRequest($input: CreateDataIngestionRunRequestInput!) {\n        createDataIngestionRunRequest(input: $input) {\n          success\n          message\n          run {\n            id\n            datasetId\n            status\n            queuedAt\n            startedAt\n            finishedAt\n          }\n        }\n      }\n    ": typeof types.CreateDataIngestionRunRequestDocument;
  "\nquery AssetGraph {\n  assetNodes {\n    assetKey {\n      path\n    }\n    dependencyKeys {\n      path\n    }\n  }\n}": typeof types.AssetGraphDocument;
  '\nquery AssetMaterializedData($assetKeys: [AssetKeyInput!] = {path: ""}) {\n  assetNodes(assetKeys: $assetKeys) {\n    assetKey {\n      path\n    }\n    partitionStats {\n      numFailed\n      numMaterialized\n      numMaterializing\n      numPartitions\n    }\n    assetPartitionStatuses {\n      ... on TimePartitionStatuses {\n        __typename\n        ranges {\n          endKey\n          startKey\n          status\n        }\n      }\n    }\n    assetMaterializations(limit: 1) {\n      runOrError {\n        ... on Run {\n          endTime\n        }\n      }\n    }\n  }\n}': typeof types.AssetMaterializedDataDocument;
  "\n  query TimeseriesMetricsByArtifact(\n    $artifactIds: [String!],\n    $metricIds: [String!],\n    $startDate: Oso_Date!,\n    $endDate: Oso_Date!, \n  ) {\n    oso_timeseriesMetricsByArtifactV0(where: {\n      artifactId: {_in: $artifactIds},\n      metricId: {_in: $metricIds},\n      sampleDate: { _gte: $startDate, _lte: $endDate }\n    }) {\n      amount\n      artifactId\n      metricId\n      sampleDate\n      unit\n    }\n    oso_artifactsV1(where: { artifactId: { _in: $artifactIds }}) {\n      artifactId\n      artifactSource\n      artifactNamespace\n      artifactName\n    }\n    oso_metricsV0(where: {metricId: {_in: $metricIds}}) {\n      metricId\n      metricSource\n      metricNamespace\n      metricName\n      displayName\n      description\n    }\n  }\n": typeof types.TimeseriesMetricsByArtifactDocument;
  "\n  query TimeseriesMetricsByProject(\n    $projectIds: [String!],\n    $metricIds: [String!],\n    $startDate: Oso_Date!,\n    $endDate: Oso_Date!, \n  ) {\n    oso_timeseriesMetricsByProjectV0(where: {\n      projectId: {_in: $projectIds},\n      metricId: {_in: $metricIds},\n      sampleDate: { _gte: $startDate, _lte: $endDate }\n    }) {\n      amount\n      metricId\n      projectId\n      sampleDate\n      unit\n    }\n    oso_projectsV1(where: { projectId: { _in: $projectIds }}) {\n      projectId\n      projectSource\n      projectNamespace\n      projectName\n      displayName\n      description\n    }\n    oso_metricsV0(where: {metricId: {_in: $metricIds}}) {\n      metricId\n      metricSource\n      metricNamespace\n      metricName\n      displayName\n      description\n    }\n  }\n": typeof types.TimeseriesMetricsByProjectDocument;
  "\n  query TimeseriesMetricsByCollection(\n    $collectionIds: [String!],\n    $metricIds: [String!],\n    $startDate: Oso_Date!,\n    $endDate: Oso_Date!, \n  ) {\n    oso_timeseriesMetricsByCollectionV0(where: {\n      collectionId: {_in: $collectionIds},\n      metricId: {_in: $metricIds},\n      sampleDate: { _gte: $startDate, _lte: $endDate }\n    }) {\n      amount\n      metricId\n      collectionId\n      sampleDate\n      unit\n    }\n    oso_collectionsV1(where: { collectionId: { _in: $collectionIds }}) {\n      collectionId\n      collectionSource\n      collectionNamespace\n      collectionName\n      displayName\n      description\n    }\n    oso_metricsV0(where: {metricId: {_in: $metricIds}}) {\n      metricId\n      metricSource\n      metricNamespace\n      metricName\n      displayName\n      description\n    }\n  }\n": typeof types.TimeseriesMetricsByCollectionDocument;
};
const documents: Documents = {
  "\n  query GetPreviewData($datasetId: ID!, $tableName: String!) {\n    datasets(where: { id: { eq: $datasetId } }, single: true) {\n      edges {\n        node {\n          id\n          typeDefinition {\n            __typename\n            ... on DataModelDefinition {\n              dataModels(where: { name: { eq: $tableName } }, single: true) {\n                edges {\n                  node {\n                    id\n                    name\n                    previewData {\n                        isAvailable\n                        rows\n                    }\n                  }\n                }\n              }\n            }\n            ... on StaticModelDefinition {\n              staticModels(where: { name: { eq: $tableName } }, single: true) {\n                edges {\n                  node {\n                    id\n                    name\n                    previewData {\n                      isAvailable\n                      rows\n                    }\n                  }\n                }\n              }\n            }\n            ... on DataIngestionDefinition {\n              dataIngestion {\n                id\n                previewData(tableName: $tableName) {\n                  isAvailable\n                  rows\n                }\n              }\n            }\n            ... on DataConnectionDefinition {\n              dataConnectionAlias {\n                id\n                schema\n                previewData(tableName: $tableName) {\n                  isAvailable\n                  rows\n                }\n              }\n            }\n          }\n        }\n      }\n    }\n  }\n":
    types.GetPreviewDataDocument,
  "\n      mutation PublishNotebook($notebookId: ID!) {\n        publishNotebook(notebookId: $notebookId) {\n          success\n          message\n          run {\n            id\n          }\n        }\n      }\n    ":
    types.PublishNotebookDocument,
  "\n      mutation UnpublishNotebook($notebookId: ID!) {\n        unpublishNotebook(notebookId: $notebookId) {\n          success\n          message\n        }\n      }\n    ":
    types.UnpublishNotebookDocument,
  "\n      mutation CreateDataConnection($input: CreateDataConnectionInput!) {\n        createDataConnection(input: $input) {\n          success\n          message\n          dataConnection {\n            id\n            orgId\n            name\n            type\n            config\n          }\n        }\n      }\n    ":
    types.CreateDataConnectionDocument,
  "\n      mutation DeleteDataConnection($id: ID!) {\n        deleteDataConnection(id: $id) {\n          success\n          message\n        }\n      }\n    ":
    types.DeleteDataConnectionDocument,
  "\n      mutation SyncDataConnection($id: ID!) {\n        syncDataConnection(id: $id) {\n          success\n          message\n          run {\n            id\n          }\n        }\n      }\n    ":
    types.SyncDataConnectionDocument,
  "\n      mutation SavePreview($input: SaveNotebookPreviewInput!) {\n        saveNotebookPreview(input: $input) {\n          success\n          message\n        }\n      }\n    ":
    types.SavePreviewDocument,
  "\n      mutation CreateDataset($input: CreateDatasetInput!) {\n        createDataset(input: $input) {\n          success\n          message\n          dataset {\n            id\n            name\n            displayName\n            description\n            type\n          }\n        }\n      }\n    ":
    types.CreateDatasetDocument,
  "\n      mutation UpdateDataset($input: UpdateDatasetInput!) {\n        updateDataset(input: $input) {\n          success\n          message\n          dataset {\n            id\n            name\n            displayName\n            description\n          }\n        }\n      }\n    ":
    types.UpdateDatasetDocument,
  "\n      mutation DeleteDataset($id: ID!) {\n        deleteDataset(id: $id) {\n          success\n          message\n        }\n      }\n    ":
    types.DeleteDatasetDocument,
  "\n      mutation CreateDataModel($input: CreateDataModelInput!) {\n        createDataModel(input: $input) {\n          success\n          message\n          dataModel {\n            id\n            name\n            isEnabled\n          }\n        }\n      }\n    ":
    types.CreateDataModelDocument,
  "\n      mutation UpdateDataModel($input: UpdateDataModelInput!) {\n        updateDataModel(input: $input) {\n          success\n          message\n          dataModel {\n            id\n            name\n            isEnabled\n          }\n        }\n      }\n    ":
    types.UpdateDataModelDocument,
  "\n      mutation DeleteDataModel($id: ID!) {\n        deleteDataModel(id: $id) {\n          success\n          message\n        }\n      }\n    ":
    types.DeleteDataModelDocument,
  "\n      mutation CreateDataModelRevision($input: CreateDataModelRevisionInput!) {\n        createDataModelRevision(input: $input) {\n          success\n          message\n          dataModelRevision {\n            id\n            createdAt\n            revisionNumber\n          }\n        }\n      }\n    ":
    types.CreateDataModelRevisionDocument,
  "\n      mutation CreateDataModelRelease($input: CreateDataModelReleaseInput!) {\n        createDataModelRelease(input: $input) {\n          success\n          message\n          dataModelRelease {\n            id\n          }\n        }\n      }\n    ":
    types.CreateDataModelReleaseDocument,
  "\n      mutation UpdateModelContext($input: UpdateModelContextInput!) {\n        updateModelContext(input: $input) {\n          success\n          message\n          modelContext {\n            id\n            context\n            columnContext {\n              name\n              context\n            }\n          }\n        }\n      }\n    ":
    types.UpdateModelContextDocument,
  "\n      mutation CreateStaticModel($input: CreateStaticModelInput!) {\n        createStaticModel(input: $input) {\n          success\n          message\n          staticModel {\n            id\n            name\n          }\n        }\n      }\n    ":
    types.CreateStaticModelDocument,
  "\n      mutation UpdateStaticModel($input: UpdateStaticModelInput!) {\n        updateStaticModel(input: $input) {\n          success\n          message\n          staticModel {\n            id\n            name\n          }\n        }\n      }\n    ":
    types.UpdateStaticModelDocument,
  "\n      mutation DeleteStaticModel($id: ID!) {\n        deleteStaticModel(id: $id) {\n          success\n          message\n        }\n      }\n    ":
    types.DeleteStaticModelDocument,
  "\n      mutation CreateUserModelRunRequest($input: CreateUserModelRunRequestInput!) {\n        createUserModelRunRequest(input: $input) {\n          success\n          message\n          run {\n            id\n          }\n        }\n      }\n    ":
    types.CreateUserModelRunRequestDocument,
  "\n      mutation CreateStaticModelRunRequest($input: CreateStaticModelRunRequestInput!) {\n        createStaticModelRunRequest(input: $input) {\n          success\n          message\n          run {\n            id\n          }\n        }\n      }\n    ":
    types.CreateStaticModelRunRequestDocument,
  "\n      mutation CreateDataIngestionConfig($input: CreateDataIngestionInput!) {\n        createDataIngestionConfig(input: $input) {\n          id\n          datasetId\n          factoryType\n          config\n          createdAt\n          updatedAt\n        }\n      }\n    ":
    types.CreateDataIngestionConfigDocument,
  "\n      mutation CreateDataIngestionRunRequest($input: CreateDataIngestionRunRequestInput!) {\n        createDataIngestionRunRequest(input: $input) {\n          success\n          message\n          run {\n            id\n            datasetId\n            status\n            queuedAt\n            startedAt\n            finishedAt\n          }\n        }\n      }\n    ":
    types.CreateDataIngestionRunRequestDocument,
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
  source: "\n  query GetPreviewData($datasetId: ID!, $tableName: String!) {\n    datasets(where: { id: { eq: $datasetId } }, single: true) {\n      edges {\n        node {\n          id\n          typeDefinition {\n            __typename\n            ... on DataModelDefinition {\n              dataModels(where: { name: { eq: $tableName } }, single: true) {\n                edges {\n                  node {\n                    id\n                    name\n                    previewData {\n                        isAvailable\n                        rows\n                    }\n                  }\n                }\n              }\n            }\n            ... on StaticModelDefinition {\n              staticModels(where: { name: { eq: $tableName } }, single: true) {\n                edges {\n                  node {\n                    id\n                    name\n                    previewData {\n                      isAvailable\n                      rows\n                    }\n                  }\n                }\n              }\n            }\n            ... on DataIngestionDefinition {\n              dataIngestion {\n                id\n                previewData(tableName: $tableName) {\n                  isAvailable\n                  rows\n                }\n              }\n            }\n            ... on DataConnectionDefinition {\n              dataConnectionAlias {\n                id\n                schema\n                previewData(tableName: $tableName) {\n                  isAvailable\n                  rows\n                }\n              }\n            }\n          }\n        }\n      }\n    }\n  }\n",
): (typeof documents)["\n  query GetPreviewData($datasetId: ID!, $tableName: String!) {\n    datasets(where: { id: { eq: $datasetId } }, single: true) {\n      edges {\n        node {\n          id\n          typeDefinition {\n            __typename\n            ... on DataModelDefinition {\n              dataModels(where: { name: { eq: $tableName } }, single: true) {\n                edges {\n                  node {\n                    id\n                    name\n                    previewData {\n                        isAvailable\n                        rows\n                    }\n                  }\n                }\n              }\n            }\n            ... on StaticModelDefinition {\n              staticModels(where: { name: { eq: $tableName } }, single: true) {\n                edges {\n                  node {\n                    id\n                    name\n                    previewData {\n                      isAvailable\n                      rows\n                    }\n                  }\n                }\n              }\n            }\n            ... on DataIngestionDefinition {\n              dataIngestion {\n                id\n                previewData(tableName: $tableName) {\n                  isAvailable\n                  rows\n                }\n              }\n            }\n            ... on DataConnectionDefinition {\n              dataConnectionAlias {\n                id\n                schema\n                previewData(tableName: $tableName) {\n                  isAvailable\n                  rows\n                }\n              }\n            }\n          }\n        }\n      }\n    }\n  }\n"];
/**
 * The gql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function gql(
  source: "\n      mutation PublishNotebook($notebookId: ID!) {\n        publishNotebook(notebookId: $notebookId) {\n          success\n          message\n          run {\n            id\n          }\n        }\n      }\n    ",
): (typeof documents)["\n      mutation PublishNotebook($notebookId: ID!) {\n        publishNotebook(notebookId: $notebookId) {\n          success\n          message\n          run {\n            id\n          }\n        }\n      }\n    "];
/**
 * The gql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function gql(
  source: "\n      mutation UnpublishNotebook($notebookId: ID!) {\n        unpublishNotebook(notebookId: $notebookId) {\n          success\n          message\n        }\n      }\n    ",
): (typeof documents)["\n      mutation UnpublishNotebook($notebookId: ID!) {\n        unpublishNotebook(notebookId: $notebookId) {\n          success\n          message\n        }\n      }\n    "];
/**
 * The gql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function gql(
  source: "\n      mutation CreateDataConnection($input: CreateDataConnectionInput!) {\n        createDataConnection(input: $input) {\n          success\n          message\n          dataConnection {\n            id\n            orgId\n            name\n            type\n            config\n          }\n        }\n      }\n    ",
): (typeof documents)["\n      mutation CreateDataConnection($input: CreateDataConnectionInput!) {\n        createDataConnection(input: $input) {\n          success\n          message\n          dataConnection {\n            id\n            orgId\n            name\n            type\n            config\n          }\n        }\n      }\n    "];
/**
 * The gql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function gql(
  source: "\n      mutation DeleteDataConnection($id: ID!) {\n        deleteDataConnection(id: $id) {\n          success\n          message\n        }\n      }\n    ",
): (typeof documents)["\n      mutation DeleteDataConnection($id: ID!) {\n        deleteDataConnection(id: $id) {\n          success\n          message\n        }\n      }\n    "];
/**
 * The gql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function gql(
  source: "\n      mutation SyncDataConnection($id: ID!) {\n        syncDataConnection(id: $id) {\n          success\n          message\n          run {\n            id\n          }\n        }\n      }\n    ",
): (typeof documents)["\n      mutation SyncDataConnection($id: ID!) {\n        syncDataConnection(id: $id) {\n          success\n          message\n          run {\n            id\n          }\n        }\n      }\n    "];
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
  source: "\n      mutation CreateDataset($input: CreateDatasetInput!) {\n        createDataset(input: $input) {\n          success\n          message\n          dataset {\n            id\n            name\n            displayName\n            description\n            type\n          }\n        }\n      }\n    ",
): (typeof documents)["\n      mutation CreateDataset($input: CreateDatasetInput!) {\n        createDataset(input: $input) {\n          success\n          message\n          dataset {\n            id\n            name\n            displayName\n            description\n            type\n          }\n        }\n      }\n    "];
/**
 * The gql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function gql(
  source: "\n      mutation UpdateDataset($input: UpdateDatasetInput!) {\n        updateDataset(input: $input) {\n          success\n          message\n          dataset {\n            id\n            name\n            displayName\n            description\n          }\n        }\n      }\n    ",
): (typeof documents)["\n      mutation UpdateDataset($input: UpdateDatasetInput!) {\n        updateDataset(input: $input) {\n          success\n          message\n          dataset {\n            id\n            name\n            displayName\n            description\n          }\n        }\n      }\n    "];
/**
 * The gql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function gql(
  source: "\n      mutation DeleteDataset($id: ID!) {\n        deleteDataset(id: $id) {\n          success\n          message\n        }\n      }\n    ",
): (typeof documents)["\n      mutation DeleteDataset($id: ID!) {\n        deleteDataset(id: $id) {\n          success\n          message\n        }\n      }\n    "];
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
  source: "\n      mutation DeleteDataModel($id: ID!) {\n        deleteDataModel(id: $id) {\n          success\n          message\n        }\n      }\n    ",
): (typeof documents)["\n      mutation DeleteDataModel($id: ID!) {\n        deleteDataModel(id: $id) {\n          success\n          message\n        }\n      }\n    "];
/**
 * The gql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function gql(
  source: "\n      mutation CreateDataModelRevision($input: CreateDataModelRevisionInput!) {\n        createDataModelRevision(input: $input) {\n          success\n          message\n          dataModelRevision {\n            id\n            createdAt\n            revisionNumber\n          }\n        }\n      }\n    ",
): (typeof documents)["\n      mutation CreateDataModelRevision($input: CreateDataModelRevisionInput!) {\n        createDataModelRevision(input: $input) {\n          success\n          message\n          dataModelRevision {\n            id\n            createdAt\n            revisionNumber\n          }\n        }\n      }\n    "];
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
  source: "\n      mutation UpdateModelContext($input: UpdateModelContextInput!) {\n        updateModelContext(input: $input) {\n          success\n          message\n          modelContext {\n            id\n            context\n            columnContext {\n              name\n              context\n            }\n          }\n        }\n      }\n    ",
): (typeof documents)["\n      mutation UpdateModelContext($input: UpdateModelContextInput!) {\n        updateModelContext(input: $input) {\n          success\n          message\n          modelContext {\n            id\n            context\n            columnContext {\n              name\n              context\n            }\n          }\n        }\n      }\n    "];
/**
 * The gql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function gql(
  source: "\n      mutation CreateStaticModel($input: CreateStaticModelInput!) {\n        createStaticModel(input: $input) {\n          success\n          message\n          staticModel {\n            id\n            name\n          }\n        }\n      }\n    ",
): (typeof documents)["\n      mutation CreateStaticModel($input: CreateStaticModelInput!) {\n        createStaticModel(input: $input) {\n          success\n          message\n          staticModel {\n            id\n            name\n          }\n        }\n      }\n    "];
/**
 * The gql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function gql(
  source: "\n      mutation UpdateStaticModel($input: UpdateStaticModelInput!) {\n        updateStaticModel(input: $input) {\n          success\n          message\n          staticModel {\n            id\n            name\n          }\n        }\n      }\n    ",
): (typeof documents)["\n      mutation UpdateStaticModel($input: UpdateStaticModelInput!) {\n        updateStaticModel(input: $input) {\n          success\n          message\n          staticModel {\n            id\n            name\n          }\n        }\n      }\n    "];
/**
 * The gql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function gql(
  source: "\n      mutation DeleteStaticModel($id: ID!) {\n        deleteStaticModel(id: $id) {\n          success\n          message\n        }\n      }\n    ",
): (typeof documents)["\n      mutation DeleteStaticModel($id: ID!) {\n        deleteStaticModel(id: $id) {\n          success\n          message\n        }\n      }\n    "];
/**
 * The gql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function gql(
  source: "\n      mutation CreateUserModelRunRequest($input: CreateUserModelRunRequestInput!) {\n        createUserModelRunRequest(input: $input) {\n          success\n          message\n          run {\n            id\n          }\n        }\n      }\n    ",
): (typeof documents)["\n      mutation CreateUserModelRunRequest($input: CreateUserModelRunRequestInput!) {\n        createUserModelRunRequest(input: $input) {\n          success\n          message\n          run {\n            id\n          }\n        }\n      }\n    "];
/**
 * The gql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function gql(
  source: "\n      mutation CreateStaticModelRunRequest($input: CreateStaticModelRunRequestInput!) {\n        createStaticModelRunRequest(input: $input) {\n          success\n          message\n          run {\n            id\n          }\n        }\n      }\n    ",
): (typeof documents)["\n      mutation CreateStaticModelRunRequest($input: CreateStaticModelRunRequestInput!) {\n        createStaticModelRunRequest(input: $input) {\n          success\n          message\n          run {\n            id\n          }\n        }\n      }\n    "];
/**
 * The gql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function gql(
  source: "\n      mutation CreateDataIngestionConfig($input: CreateDataIngestionInput!) {\n        createDataIngestionConfig(input: $input) {\n          id\n          datasetId\n          factoryType\n          config\n          createdAt\n          updatedAt\n        }\n      }\n    ",
): (typeof documents)["\n      mutation CreateDataIngestionConfig($input: CreateDataIngestionInput!) {\n        createDataIngestionConfig(input: $input) {\n          id\n          datasetId\n          factoryType\n          config\n          createdAt\n          updatedAt\n        }\n      }\n    "];
/**
 * The gql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function gql(
  source: "\n      mutation CreateDataIngestionRunRequest($input: CreateDataIngestionRunRequestInput!) {\n        createDataIngestionRunRequest(input: $input) {\n          success\n          message\n          run {\n            id\n            datasetId\n            status\n            queuedAt\n            startedAt\n            finishedAt\n          }\n        }\n      }\n    ",
): (typeof documents)["\n      mutation CreateDataIngestionRunRequest($input: CreateDataIngestionRunRequestInput!) {\n        createDataIngestionRunRequest(input: $input) {\n          success\n          message\n          run {\n            id\n            datasetId\n            status\n            queuedAt\n            startedAt\n            finishedAt\n          }\n        }\n      }\n    "];
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
