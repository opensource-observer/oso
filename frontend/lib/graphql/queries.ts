import { gql } from "../__generated__/gql";

// Max TTL on Hasura is 300 seconds
// https://hasura.io/docs/latest/caching/caching-config/#controlling-cache-lifetime/

/**********************
 * ARTIFACT
 **********************/

const GET_ALL_ARTIFACTS = gql(`
  query Artifacts @cached (ttl: 300) {
    artifact {
      id
      name
      namespace
    }
  }
`);

const GET_ARTIFACTS_BY_IDS = gql(`
  query ArtifactsByIds($artifactIds: [Int!]) @cached (ttl: 300)  {
    artifact(where: { id: { _in: $artifactIds } }) {
      id
      name
      namespace
    }
  }
`);

const GET_ARTIFACT_BY_NAME = gql(`
  query ArtifactByName($namespace: artifact_namespace_enum!, $name: String!) @cached(ttl: 300) {
    artifact(where: { name: { _eq: $name }, namespace: { _eq: $namespace } }) {
      id
      name
      namespace
      type
      url
    }
  }
`);

/**********************
 * PROJECT
 **********************/

const GET_ALL_PROJECTS = gql(`
  query Projects @cached(ttl: 300) {
    project {
      id
      name
      slug
    }
  }
`);

const GET_PROJECTS_BY_IDS = gql(`
  query ProjectsByIds($projectIds: [Int!]) @cached(ttl: 300) {
    project(where: { id: { _in: $projectIds } }) {
      id
      name
      slug
    }
  }
`);

const GET_PROJECTS_BY_SLUGS = gql(`
  query ProjectsBySlug($slugs: [String!]) @cached(ttl: 300) {
    project(where: { slug: { _in: $slugs } }) {
      id
      name
      slug
      description
      verified
    }
  }
`);

const GET_PROJECTS_BY_COLLECTION_SLUGS = gql(`
  query ProjectsByCollectionSlugs($slugs: [String!]) @cached(ttl: 300) {
    project(where: {collection_projects_projects: {collection: {slug: {_in: $slugs}}}}) {
      id
      name
      slug
      description
      verified
    }
  }
`);

/**********************
 * COLLECTION
 **********************/

const GET_ALL_COLLECTIONS = gql(`
  query Collections @cached(ttl: 300) {
    collection {
      id
      name
      slug
    }
  }
`);

const GET_COLLECTIONS_BY_IDS = gql(`
  query CollectionsByIds($collectionIds: [Int!]) @cached(ttl: 300) {
    collection(where: { id: { _in: $collectionIds } }) {
      id
      name
      slug
    }
  }
`);

const GET_COLLECTIONS_BY_SLUGS = gql(`
  query CollectionsBySlug($slugs: [String!]) @cached(ttl: 300) {
    collection(where: { slug: { _in: $slugs } }) {
      id
      name
      slug
      description
      verified
    }
  }
`);

/**********************
 * EVENTS
 **********************/

const GET_ALL_EVENT_TYPES = gql(`
  query GetAllEventTypes @cached(ttl: 300) {
    event_type {
      id
      name
    }
  }
`);

const GET_EVENT_TYPES_BY_IDS = gql(`
  query EventTypesByIds($typeIds: [Int!]) @cached(ttl: 300) {
    event_type(where: {id: {_in: $typeIds}}) {
      id
      name
    }
  }
`);

const GET_EVENTS_DAILY_TO_ARTIFACT = gql(`
  query EventsDailyToArtifact(
    $artifactIds: [Int!],
    $typeIds: [Int!],
    $startDate: timestamptz!,
    $endDate: timestamptz!, 
  ) {
    events_daily_to_artifact(where: {
      artifactId: { _in: $artifactIds },
      typeId: { _in: $typeIds },
      bucketDaily: { _gte: $startDate, _lte: $endDate }
    }) {
      typeId
      artifactId
      bucketDaily
      amount
    }
  }
`);

const GET_EVENTS_WEEKLY_TO_ARTIFACT = gql(`
  query EventsWeeklyToArtifact(
    $artifactIds: [Int!],
    $typeIds: [Int!],
    $startDate: timestamptz!,
    $endDate: timestamptz!, 
  ) {
    events_weekly_to_artifact(where: {
      artifactId: { _in: $artifactIds },
      typeId: { _in: $typeIds },
      bucketWeekly: { _gte: $startDate, _lte: $endDate }
    }) {
      typeId
      artifactId
      bucketWeekly
      amount
    }
  }
`);

const GET_EVENTS_MONTHLY_TO_ARTIFACT = gql(`
  query EventsMonthlyToArtifact(
    $artifactIds: [Int!],
    $typeIds: [Int!],
    $startDate: timestamptz!,
    $endDate: timestamptz!, 
  ) {
    events_monthly_to_artifact(where: {
      artifactId: { _in: $artifactIds },
      typeId: { _in: $typeIds },
      bucketMonthly: { _gte: $startDate, _lte: $endDate }
    }) {
      typeId
      artifactId
      bucketMonthly
      amount
    }
  }
`);

const GET_EVENTS_DAILY_TO_COLLECTION = gql(`
  query EventsDailyToCollection(
    $collectionIds: [Int!],
    $typeIds: [Int!],
    $startDate: timestamptz!,
    $endDate: timestamptz!, 
  ) {
    events_daily_to_collection(where: {
      collectionId: { _in: $collectionIds },
      typeId: { _in: $typeIds },
      bucketDay: { _gte: $startDate, _lte: $endDate }
    }) {
      typeId
      collectionId
      bucketDay
      amount
    }
  }
`);

const GET_EVENTS_WEEKLY_TO_COLLECTION = gql(`
  query EventsWeeklyToCollection(
    $collectionIds: [Int!],
    $typeIds: [Int!],
    $startDate: timestamptz!,
    $endDate: timestamptz!, 
  ) {
    events_weekly_to_collection(where: {
      collectionId: { _in: $collectionIds },
      typeId: { _in: $typeIds },
      bucketWeekly: { _gte: $startDate, _lte: $endDate }
    }) {
      typeId
      collectionId
      bucketWeekly
      amount
    }
  }
`);

const GET_EVENTS_MONTHLY_TO_COLLECTION = gql(`
  query EventsMonthlyToCollection(
    $collectionIds: [Int!],
    $typeIds: [Int!],
    $startDate: timestamptz!,
    $endDate: timestamptz!, 
  ) {
    events_monthly_to_collection(where: {
      collectionId: { _in: $collectionIds },
      typeId: { _in: $typeIds },
      bucketMonthly: { _gte: $startDate, _lte: $endDate }
    }) {
      typeId
      collectionId
      bucketMonthly
      amount
    }
  }
`);

const GET_EVENTS_DAILY_TO_PROJECT = gql(`
  query EventsDailyToProject(
    $projectIds: [Int!],
    $typeIds: [Int!],
    $startDate: timestamptz!,
    $endDate: timestamptz!, 
  ) {
    events_daily_to_project(where: {
      projectId: { _in: $projectIds },
      typeId: { _in: $typeIds },
      bucketDaily: { _gte: $startDate, _lte: $endDate }
    }) {
      typeId
      projectId
      bucketDaily
      amount
    }
  }
`);

const GET_EVENTS_WEEKLY_TO_PROJECT = gql(`
  query EventsWeeklyToProject(
    $projectIds: [Int!],
    $typeIds: [Int!],
    $startDate: timestamptz!,
    $endDate: timestamptz!, 
  ) {
    events_weekly_to_project(where: {
      projectId: { _in: $projectIds },
      typeId: { _in: $typeIds },
      bucketWeekly: { _gte: $startDate, _lte: $endDate }
    }) {
      typeId
      projectId
      bucketWeekly
      amount
    }
  }
`);

const GET_EVENTS_MONTHLY_TO_PROJECT = gql(`
  query EventsMonthlyToProject(
    $projectIds: [Int!],
    $typeIds: [Int!],
    $startDate: timestamptz!,
    $endDate: timestamptz!, 
  ) {
    events_monthly_to_project(where: {
      projectId: { _in: $projectIds },
      typeId: { _in: $typeIds },
      bucketMonthly: { _gte: $startDate, _lte: $endDate }
    }) {
      typeId
      projectId
      bucketMonthly
      amount
    }
  }
`);

const GET_USERS_MONTHLY_TO_PROJECT = gql(`
  query UsersMonthlyToProject(
    $projectIds: [Int!],
    $segmentTypes: [String!],
    $startDate: timestamptz!,
    $endDate: timestamptz!, 
  ) {
    users_monthly_to_project(where: {
      projectId: { _in: $projectIds },
      segmentType: { _in: $segmentTypes },
      bucketMonthly: { _gte: $startDate, _lte: $endDate }
    }) {
      segmentType
      projectId
      bucketMonthly
      amount
    }
  }
`);

const GET_EVENT_SUM = gql(`
  query AggregateSum (
    $projectIds: [Int!],
    $typeIds: [Int!],
    $startDate: timestamptz!,
    $endDate: timestamptz!, 
  ) @cached(ttl: 300) {
    events_monthly_to_project_aggregate(
      where: {
        projectId: {_in: $projectIds},
        typeId: {_in: $typeIds},
        bucketMonthly: {_gte: $startDate, _lte: $endDate}}
    ) {
      aggregate {
        sum {
          amount
        }
      }
    }
  }
`);

export {
  GET_ALL_ARTIFACTS,
  GET_ARTIFACTS_BY_IDS,
  GET_ARTIFACT_BY_NAME,
  GET_ALL_PROJECTS,
  GET_PROJECTS_BY_IDS,
  GET_PROJECTS_BY_SLUGS,
  GET_PROJECTS_BY_COLLECTION_SLUGS,
  GET_ALL_COLLECTIONS,
  GET_COLLECTIONS_BY_IDS,
  GET_COLLECTIONS_BY_SLUGS,
  GET_ALL_EVENT_TYPES,
  GET_EVENT_TYPES_BY_IDS,
  GET_EVENTS_DAILY_TO_ARTIFACT,
  GET_EVENTS_WEEKLY_TO_ARTIFACT,
  GET_EVENTS_MONTHLY_TO_ARTIFACT,
  GET_EVENTS_DAILY_TO_PROJECT,
  GET_EVENTS_WEEKLY_TO_PROJECT,
  GET_EVENTS_MONTHLY_TO_PROJECT,
  GET_EVENTS_DAILY_TO_COLLECTION,
  GET_EVENTS_WEEKLY_TO_COLLECTION,
  GET_EVENTS_MONTHLY_TO_COLLECTION,
  GET_USERS_MONTHLY_TO_PROJECT,
  GET_EVENT_SUM,
};
