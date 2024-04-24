import { cache } from "react";
import { getApolloClient } from "../clients/apollo";
import { QueryOptions } from "@apollo/client";
import {
  GET_ARTIFACTS_BY_IDS,
  GET_ARTIFACT_BY_NAME,
  GET_ARTIFACT_IDS_BY_PROJECT_IDS,
  GET_PROJECTS_BY_SLUGS,
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
  const client = getApolloClient();
  try {
    const { data, error } = await client.query(opts);
    if (error) {
      logger.error("Server-side Apollo Client error: ", error);
      throw error;
    }
    return data;
  } catch (error) {
    logger.error("Server-side Apollo Client error: ", error);
    throw error;
  }
};

// Cached getters
const cachedGetAllEventTypes = cache(async () =>
  queryWrapper({
    query: GET_ALL_EVENT_TYPES,
  }),
);

const cachedGetProjectsBySlugs = cache(
  async (variables: { project_slugs: string[] }) =>
    queryWrapper({
      query: GET_PROJECTS_BY_SLUGS,
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
    artifact_namespace: string;
    artifact_type: string;
    artifact_name: string;
  }) =>
    queryWrapper({
      query: GET_ARTIFACT_BY_NAME,
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
  cachedGetProjectsBySlugs,
  cachedGetCollectionsByIds,
  cachedGetCollectionIdsByProjectIds,
  cachedGetCodeMetricsByProjectIds,
  cachedGetOnchainMetricsByProjectIds,
  cachedGetAllEventTypes,
};
