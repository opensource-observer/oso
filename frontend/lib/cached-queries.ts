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
    }
    return data;
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
  }
  return data;
});

export { cachedGetArtifactByName, cachedGetProjectBySlug };
