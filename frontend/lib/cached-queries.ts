import { cache } from "react";
import { getApolloClient } from "./clients/apollo";
import { GET_ARTIFACT_BY_NAME, GET_PROJECT_BY_SLUG } from "./graphql/queries";
import { logger } from "./logger";

// Revalidate the data at most every hour
export const revalidate = 3600;

// Cached getters
const cachedGetArtifactByName = cache(
  async (namespace: string, name: string) => {
    const { data, error } = await getApolloClient().query({
      query: GET_ARTIFACT_BY_NAME,
      variables: {
        namespace,
        name,
      },
    });

    if (error) {
      logger.error(error);
      return null;
    } else if (
      !data?.artifact ||
      !Array.isArray(data.artifact) ||
      data.artifact.length < 1
    ) {
      return null;
    }
    return data.artifact[0];
  },
);

const cachedGetProjectBySlug = cache(async (slug: string) => {
  const { data, error } = await getApolloClient().query({
    query: GET_PROJECT_BY_SLUG,
    variables: {
      slug,
    },
  });

  if (error) {
    logger.error(error);
    return null;
  } else if (
    !data?.project ||
    !Array.isArray(data.project) ||
    data.project.length < 1
  ) {
    return null;
  }
  return data.project[0];
});

export { cachedGetArtifactByName, cachedGetProjectBySlug };
