import { gql } from "../__generated__/gql";

// Max TTL on Hasura is 300 seconds
// https://hasura.io/docs/latest/caching/caching-config/#controlling-cache-lifetime/

/**********************
 * ARTIFACT / PROJECT / COLLECTION
 **********************/

const GET_ARTIFACTS_BY_IDS = gql(`
  query ArtifactByIds($artifact_ids: [String!]) @cached(ttl: 300) {
    artifacts_v1(where: { artifact_id: { _in: $artifact_ids }}) {
      artifact_id
      artifact_source
      artifact_namespace
      artifact_name
      artifact_url
    }
  }
`);

const GET_PROJECTS_BY_IDS = gql(`
  query ProjectsByIds($project_ids: [String!]) @cached(ttl: 300) {
    projects_v1(where: { project_id: { _in: $project_ids }}) {
      project_id
      project_source
      project_namespace
      project_name
      display_name
      description
    }
  }
`);

const GET_COLLECTIONS_BY_IDS = gql(`
  query CollectionsByIds($collection_ids: [String!]) @cached(ttl: 300) {
    collections_v1(where: { collection_id: { _in: $collection_ids }}) {
      collection_id
      collection_source
      collection_namespace
      collection_name
      display_name
      description
    }
  }
`);

const GET_ALL_EVENT_TYPES = gql(`
  query GetAllEventTypes @cached(ttl: 300) {
    event_types_v1 {
      event_type
    }
  }
`);

export {
  GET_ARTIFACTS_BY_IDS,
  GET_PROJECTS_BY_IDS,
  GET_COLLECTIONS_BY_IDS,
  GET_ALL_EVENT_TYPES,
};
