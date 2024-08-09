import { gql } from "../__generated__/gql";

// Max TTL on Hasura is 300 seconds
// https://hasura.io/docs/latest/caching/caching-config/#controlling-cache-lifetime/

/**********************
 * ARTIFACT / PROJECT / COLLECTION
 **********************/

const GET_ARTIFACTS_BY_IDS = gql(`
  query ArtifactByIds($artifactIds: [String!]) {
    oso_artifactsV1(where: { artifactId: { _in: $artifactIds }}) {
      artifactId
      artifactSource
      artifactNamespace
      artifactName
      artifactUrl
    }
  }
`);

const GET_PROJECTS_BY_IDS = gql(`
  query ProjectsByIds($projectIds: [String!]) @cached(ttl: 300) {
    oso_projectsV1(where: { projectId: { _in: $projectIds }}) {
      projectId
      projectSource
      projectNamespace
      projectName
      displayName
      description
    }
  }
`);

const GET_COLLECTIONS_BY_IDS = gql(`
  query CollectionsByIds($collectionIds: [String!]) @cached(ttl: 300) {
    oso_collectionsV1(where: { collectionId: { _in: $collectionIds }}) {
      collectionId
      collectionSource
      collectionNamespace
      collectionName
      displayName
      description
    }
  }
`);

const GET_ALL_EVENT_TYPES = gql(`
  query GetAllEventTypes @cached(ttl: 300) {
    oso_eventTypesV1 {
      eventType
    }
  }
`);

export {
  GET_ARTIFACTS_BY_IDS,
  GET_PROJECTS_BY_IDS,
  GET_COLLECTIONS_BY_IDS,
  GET_ALL_EVENT_TYPES,
};
