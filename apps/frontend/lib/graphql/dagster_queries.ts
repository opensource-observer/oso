import { gql } from "@/lib/graphql/generated";

const GET_ASSETS_GRAPH = gql(`
query AssetGraph {
  assetNodes {
    assetKey {
      path
    }
    dependencyKeys {
      path
    }
  }
}`);

const GET_ASSETS_MATERIALIZED_DATA = gql(`
query AssetMaterializedData($assetKeys: [AssetKeyInput!] = {path: ""}) {
  assetNodes(assetKeys: $assetKeys) {
    assetKey {
      path
    }
    partitionStats {
      numFailed
      numMaterialized
      numMaterializing
      numPartitions
    }
    assetPartitionStatuses {
      ... on TimePartitionStatuses {
        __typename
        ranges {
          endKey
          startKey
          status
        }
      }
    }
    assetMaterializations(limit: 1) {
      runOrError {
        ... on Run {
          endTime
        }
      }
    }
  }
}`);

export { GET_ASSETS_GRAPH, GET_ASSETS_MATERIALIZED_DATA };
