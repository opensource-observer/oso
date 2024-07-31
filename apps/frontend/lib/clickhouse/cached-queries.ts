// Maintains the same interface as a previous graphql iteration of this

import { cache } from "react";
import {
  GET_ARTIFACTS_BY_IDS,
  GET_ARTIFACT_BY_SOURCE_NAMESPACE_NAME,
  GET_ARTIFACT_BY_SOURCE_NAME,
  GET_ARTIFACT_IDS_BY_PROJECT_IDS,
  GET_PROJECT_BY_NAME,
  GET_COLLECTIONS_BY_IDS,
  GET_COLLECTION_IDS_BY_PROJECT_IDS,
  GET_CODE_METRICS_BY_PROJECT,
  GET_ONCHAIN_METRICS_BY_PROJECT,
  GET_ALL_EVENT_TYPES,
} from "./queries";
import { getClickhouseClient } from "../clients/clickhouse";

interface QueryOptions {
  query: string;
  variables?: Record<string, any>;
}

const queryWrapper = async (opts: QueryOptions) => {
  const client = getClickhouseClient();
  const rows = await client.query({
    query: opts.query,
    query_params: opts.variables,
  });
  return rows.json();
};

// Cached getters
const cachedGetAllEventTypes = cache(async () =>
  queryWrapper({
    query: GET_ALL_EVENT_TYPES,
  }),
);

const cachedGetProjectByName = cache(
  async (variables: { projectName: string }) =>
    queryWrapper({
      query: GET_PROJECT_BY_NAME,
      variables,
    }),
);

const cachedGetArtifactsByIds = cache(
  async (variables: { artifactIds: string[] }) =>
    queryWrapper({
      query: GET_ARTIFACTS_BY_IDS,
      variables,
    }),
);

const cachedGetArtifactByName = cache(
  async (variables: {
    artifactSource: string;
    artifactNamespace?: string;
    artifactName: string;
  }) =>
    variables.artifactNamespace
      ? queryWrapper({
          query: GET_ARTIFACT_BY_SOURCE_NAMESPACE_NAME,
          variables,
        })
      : queryWrapper({
          query: GET_ARTIFACT_BY_SOURCE_NAME,
          variables,
        }),
);

const cachedGetArtifactIdsByProjectIds = cache(
  async (variables: { projectIds: string[] }) =>
    queryWrapper({
      query: GET_ARTIFACT_IDS_BY_PROJECT_IDS,
      variables,
    }),
);

const cachedGetCollectionsByIds = cache(
  async (variables: { collectionIds: string[] }) =>
    queryWrapper({
      query: GET_COLLECTIONS_BY_IDS,
      variables,
    }),
);

const cachedGetCollectionIdsByProjectIds = cache(
  async (variables: { projectIds: string[] }) =>
    queryWrapper({
      query: GET_COLLECTION_IDS_BY_PROJECT_IDS,
      variables,
    }),
);

const cachedGetCodeMetricsByProjectIds = cache(
  async (variables: { projectIds: string[] }) =>
    queryWrapper({
      query: GET_CODE_METRICS_BY_PROJECT,
      variables,
    }),
);

const cachedGetOnchainMetricsByProjectIds = cache(
  async (variables: { projectIds: string[] }) =>
    queryWrapper({
      query: GET_ONCHAIN_METRICS_BY_PROJECT,
      variables,
    }),
);

export {
  cachedGetArtifactsByIds,
  cachedGetArtifactByName,
  cachedGetArtifactIdsByProjectIds,
  cachedGetProjectByName,
  cachedGetCollectionsByIds,
  cachedGetCollectionIdsByProjectIds,
  cachedGetCodeMetricsByProjectIds,
  cachedGetOnchainMetricsByProjectIds,
  cachedGetAllEventTypes,
};
