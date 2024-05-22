import { cache } from "react";
import { getApolloClient } from "../clients/apollo";
import { QueryOptions } from "@apollo/client";
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
import { logger } from "../logger";

// Revalidate the data at most every hour
export const revalidate = false; // 3600 = 1 hour

const queryWrapper = async (opts: QueryOptions) => {
  const { data, error } = await getApolloClient().query(opts);
  if (error) {
    logger.error(error);
    throw error;
  }
  return data;
};

// Cached getters
const cachedGetAllEventTypes = cache(async () =>
  queryWrapper({
    query: GET_ALL_EVENT_TYPES,
  }),
);

const cachedGetProjectByName = cache(
  async (variables: { project_name: string }) =>
    queryWrapper({
      query: GET_PROJECT_BY_NAME,
      variables,
    }),
);

const cachedGetArtifactsByIds = cache(
  async (variables: { artifact_ids: string[] }) =>
    queryWrapper({
      query: GET_ARTIFACTS_BY_IDS,
      variables,
    }),
);

const cachedGetArtifactByName = cache(
  async (variables: {
    artifact_source: string;
    artifact_namespace?: string;
    artifact_name: string;
  }) =>
    variables.artifact_namespace
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
  async (variables: { project_ids: string[] }) =>
    queryWrapper({
      query: GET_ARTIFACT_IDS_BY_PROJECT_IDS,
      variables,
    }),
);

const cachedGetCollectionsByIds = cache(
  async (variables: { collection_ids: string[] }) =>
    queryWrapper({
      query: GET_COLLECTIONS_BY_IDS,
      variables,
    }),
);

const cachedGetCollectionIdsByProjectIds = cache(
  async (variables: { project_ids: string[] }) =>
    queryWrapper({
      query: GET_COLLECTION_IDS_BY_PROJECT_IDS,
      variables,
    }),
);

const cachedGetCodeMetricsByProjectIds = cache(
  async (variables: { project_ids: string[] }) =>
    queryWrapper({
      query: GET_CODE_METRICS_BY_PROJECT,
      variables,
    }),
);

const cachedGetOnchainMetricsByProjectIds = cache(
  async (variables: { project_ids: string[] }) =>
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
