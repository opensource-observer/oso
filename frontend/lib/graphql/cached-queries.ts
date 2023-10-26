import { cache } from "react";
import { getApolloClient } from "../clients/apollo";
import {
  GET_ALL_ARTIFACTS,
  GET_ARTIFACT_BY_NAME,
  GET_ALL_PROJECTS,
  GET_PROJECTS_BY_SLUGS,
  GET_EVENT_SUM,
  GET_EVENT_TYPES_BY_IDS,
} from "./queries";
import { logger } from "../logger";

// Revalidate the data at most every hour
export const revalidate = 3600; // 3600 = 1 hour

// Cached getters
const cachedGetAllArtifacts = cache(async () => {
  const { data, error } = await getApolloClient().query({
    query: GET_ALL_ARTIFACTS,
  });
  if (error) {
    logger.error(error);
    throw error;
  }
  return data;
});

const cachedGetArtifactByName = cache(
  async (variables: { namespace: string; name: string }) => {
    const { data, error } = await getApolloClient().query({
      query: GET_ARTIFACT_BY_NAME,
      variables,
    });
    if (error) {
      logger.error(error);
      throw error;
    }
    return data;
  },
);

const cachedGetAllProjects = cache(async () => {
  const { data, error } = await getApolloClient().query({
    query: GET_ALL_PROJECTS,
  });
  if (error) {
    logger.error(error);
    throw error;
  }
  return data;
});

const cachedGetProjectsBySlugs = cache(
  async (variables: { slugs: string[] }) => {
    const { data, error } = await getApolloClient().query({
      query: GET_PROJECTS_BY_SLUGS,
      variables,
    });
    if (error) {
      logger.error(error);
      throw error;
    }
    return data;
  },
);

const cachedGetEventTypesByIds = cache(
  async (variables: { typeIds: number[] }) => {
    const { data, error } = await getApolloClient().query({
      query: GET_EVENT_TYPES_BY_IDS,
      variables,
    });
    if (error) {
      logger.error(error);
      throw error;
    }
    return data;
  },
);

const cachedGetEventSum = cache(
  async (variables: {
    projectIds: number[];
    typeIds: number[];
    startDate: string;
    endDate: string;
  }) => {
    const { data, error } = await getApolloClient().query({
      query: GET_EVENT_SUM,
      variables,
    });
    if (error) {
      logger.error(error);
      throw error;
    }
    return data;
  },
);

export {
  cachedGetAllArtifacts,
  cachedGetArtifactByName,
  cachedGetAllProjects,
  cachedGetProjectsBySlugs,
  cachedGetEventTypesByIds,
  cachedGetEventSum,
};
