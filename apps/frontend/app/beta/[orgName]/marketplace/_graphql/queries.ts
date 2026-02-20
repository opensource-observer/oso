import { gql } from "@/lib/graphql/generated/gql";

export const RESOLVE_ORGANIZATION = gql(`
  query ResolveOrganization($where: JSON) {
    organizations(first: 1, single: true, where: $where) {
      edges {
        node {
          id
          name
        }
      }
    }
  }
`);

export const MARKETPLACE_DATASETS = gql(`
  query MarketplaceDatasets(
    $first: Int
    $after: String
    $search: String
    $datasetType: DatasetType
    $orgId: ID!
  ) {
    marketplaceDatasets(
      orgId: $orgId
      first: $first
      after: $after
      search: $search
      datasetType: $datasetType
    ) {
      edges {
        node {
          id
          name
          displayName
          description
          type
          updatedAt
          organization {
            name
            displayName
          }
          tables(first: 0) {
            totalCount
          }
          isSubscribed(orgId: $orgId)
        }
        cursor
      }
      pageInfo {
        hasNextPage
        hasPreviousPage
        startCursor
        endCursor
      }
      totalCount
    }
  }
`);

export const SUBSCRIBE_TO_DATASET = gql(`
  mutation SubscribeToDataset($input: SubscribeToDatasetInput!) {
    subscribeToDataset(input: $input) {
      success
      message
    }
  }
`);

export const UNSUBSCRIBE_FROM_DATASET = gql(`
  mutation UnsubscribeFromDataset($input: UnsubscribeFromDatasetInput!) {
    unsubscribeFromDataset(input: $input) {
      success
      message
    }
  }
`);
