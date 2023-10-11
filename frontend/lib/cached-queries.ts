import { cache } from "react";
import { getApolloClient } from "./clients/apollo";
import {
  GET_ALL_ARTIFACTS,
  GET_ARTIFACT_BY_NAME,
  GET_ALL_PROJECTS,
  GET_PROJECT_BY_SLUG,
} from "./graphql/queries";
import { logger } from "./logger";

// Revalidate the data at most every hour
export const revalidate = 3600;

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

const cachedGetProjectBySlug = cache(async (variables: { slug: string }) => {
  const { data, error } = await getApolloClient().query({
    query: GET_PROJECT_BY_SLUG,
    variables,
  });
  if (error) {
    logger.error(error);
    throw error;
  }
  return data;
});

export {
  cachedGetAllArtifacts,
  cachedGetArtifactByName,
  cachedGetAllProjects,
  cachedGetProjectBySlug,
};
