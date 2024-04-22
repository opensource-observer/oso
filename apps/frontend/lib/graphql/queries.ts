import { gql } from "../__generated__/gql";

// Max TTL on Hasura is 300 seconds
// https://hasura.io/docs/latest/caching/caching-config/#controlling-cache-lifetime/

/**********************
 * ARTIFACT
 **********************/

const GET_ALL_ARTIFACTS = gql(`
  query Artifacts @cached (ttl: 300) {
    artifacts {
      artifact_id
      artifact_namespace
      artifact_type
      artifact_source_id
      artifact_latest_name
      artifact_names
    }
  }
`);

const GET_ARTIFACTS_BY_IDS = gql(`
  query ArtifactByIds($artifact_ids: [String!]) @cached(ttl: 300) {
    artifacts(where: { artifact_id: { _in: $artifact_ids }}) {
      artifact_id
      artifact_namespace
      artifact_type
      artifact_source_id
      artifact_latest_name
      artifact_names
      artifact_url
    }
  }
`);

const GET_ARTIFACT_BY_NAME = gql(`
  query ArtifactByName($artifact_namespace: String!, $artifact_type: String!, $artifact_name: String!) @cached(ttl: 300) {
    artifacts(where: { artifact_namespace: { _eq: $artifact_namespace }, artifact_type: { _eq: $artifact_type }, artifact_latest_name: { _eq: $artifact_name } }) {
      artifact_id
      artifact_namespace
      artifact_type
      artifact_source_id
      artifact_latest_name
      artifact_names
      artifact_url
    }
  }
`);

const GET_ARTIFACT_IDS_BY_PROJECT_IDS = gql(`
  query ArtifactIdsByProjectIds($project_ids: [String!]) @cached(ttl: 300) {
    artifacts_by_project(where: { project_id: { _in: $project_ids }}) {
      artifact_id
    }
  }
`);

/**********************
 * PROJECT
 **********************/

const GET_ALL_PROJECTS = gql(`
  query Projects @cached(ttl: 300) {
    projects {
      project_id
      project_slug
      project_name
    }
  }
`);

const GET_PROJECTS_BY_IDS = gql(`
  query ProjectsByIds($project_ids: [String!]) @cached(ttl: 300) {
    projects(where: { project_id: { _in: $project_ids }}) {
      project_id
      project_slug
      project_name
    }
  }
`);

const GET_PROJECTS_BY_SLUGS = gql(`
  query ProjectsBySlugs($project_slugs: [String!]) @cached(ttl: 300) {
    projects(where: { project_slug: { _in: $project_slugs } }) {
      project_id
      project_slug
      project_name
    }
  }
`);

/**********************
 * COLLECTION
 **********************/

const GET_ALL_COLLECTIONS = gql(`
  query Collections @cached(ttl: 300) {
    collections {
      collection_id
      user_namespace
      collection_slug
      collection_name
    }
  }
`);

const GET_COLLECTIONS_BY_IDS = gql(`
  query CollectionsByIds($collection_ids: [String!]) @cached(ttl: 300) {
    collections(where: { collection_id: { _in: $collection_ids }}) {
      collection_id
      user_namespace
      collection_slug
      collection_name
    }
  }
`);

const GET_COLLECTIONS_BY_SLUGS = gql(`
  query CollectionsBySlugs($collection_slugs: [String!]) @cached(ttl: 300) {
    collections(where: { collection_slug: { _in: $collection_slugs }, user_namespace: { _eq: "oso" } }) {
      collection_id
      user_namespace
      collection_slug
      collection_name
    }
  }
`);

const GET_COLLECTION_IDS_BY_PROJECT_IDS = gql(`
  query CollectionIdsByProjectIds($project_ids: [String!]) @cached(ttl: 300) {
    projects_by_collection(where: { project_id: { _in: $project_ids }}) {
      collection_id
    }
  }
`);

/**********************
 * METRICS
 **********************/

const GET_CODE_METRICS_BY_PROJECT = gql(`
  query CodeMetricsByProject(
    $project_ids: [String!],
  ) {
    code_metrics_by_project(where: {
      project_id: { _in: $project_ids },
    }) {
      project_id
      project_name
      stars
      source
      repositories
      pull_requests_opened_6_months
      pull_requests_merged_6_months
      new_contributors_6_months
      last_commit_date
      issues_opened_6_months
      issues_closed_6_months
      avg_active_devs_6_months
      avg_fulltime_devs_6_months
      commits_6_months
      contributors
      contributors_6_months
      first_commit_date
      forks
    }
  }
`);

const GET_ONCHAIN_METRICS_BY_PROJECT = gql(`
  query OnchainMetricsByProject(
    $project_ids: [String!],
  ) {
    onchain_metrics_by_project(where: {
      project_id: { _in: $project_ids },
    }) {
      project_id
      project_name
      active_users
      first_txn_date
      high_frequency_users
      l2_gas_6_months
      less_active_users
      more_active_users
      multi_project_users
      network
      new_user_count
      num_contracts
      total_l2_gas
      total_txns
      total_users
      txns_6_months
      users_6_months
    }
  }
`);

/**********************
 * EVENTS
 **********************/

const GET_ALL_EVENT_TYPES = gql(`
  query GetAllEventTypes @cached(ttl: 300) {
    event_types {
      event_type
    }
  }
`);

const GET_EVENTS_DAILY_TO_COLLECTION = gql(`
  query EventsDailyToCollection(
    $collection_ids: [String!],
    $event_types: [String!],
    $start_date: timestamptz!,
    $end_date: timestamptz!, 
  ) {
    events_daily_to_collection(where: {
      collection_id: { _in: $collection_ids },
      event_type: { _in: $event_types },
      bucket_day: { _gte: $start_date, _lte: $end_date }
    }) {
      collection_id
      event_type
      bucket_day
      amount
    }
  }
`);

const GET_EVENTS_WEEKLY_TO_COLLECTION = gql(`
  query EventsWeeklyToCollection(
    $collection_ids: [String!],
    $event_types: [String!],
    $start_date: timestamptz!,
    $end_date: timestamptz!, 
  ) {
    events_weekly_to_collection(where: {
      collection_id: { _in: $collection_ids },
      event_type: { _in: $event_types },
      bucket_week: { _gte: $start_date, _lte: $end_date }
    }) {
      collection_id
      event_type
      bucket_week
      amount
    }
  }
`);

const GET_EVENTS_MONTHLY_TO_COLLECTION = gql(`
  query EventsMonthlyToCollection(
    $collection_ids: [String!],
    $event_types: [String!],
    $start_date: timestamptz!,
    $end_date: timestamptz!, 
  ) {
    events_monthly_to_collection(where: {
      collection_id: { _in: $collection_ids },
      event_type: { _in: $event_types },
      bucket_month: { _gte: $start_date, _lte: $end_date }
    }) {
      collection_id
      event_type
      bucket_month
      amount
    }
  }
`);

const GET_EVENTS_DAILY_TO_PROJECT = gql(`
  query EventsDailyToProject(
    $project_ids: [String!],
    $event_types: [String!],
    $start_date: timestamptz!,
    $end_date: timestamptz!, 
  ) {
    events_daily_to_project(where: {
      project_id: { _in: $project_ids },
      event_type: { _in: $event_types },
      bucket_day: { _gte: $start_date, _lte: $end_date }
    }) {
      project_id
      event_type
      bucket_day
      amount
    }
  }
`);

const GET_EVENTS_WEEKLY_TO_PROJECT = gql(`
  query EventsWeeklyToProject(
    $project_ids: [String!],
    $event_types: [String!],
    $start_date: timestamptz!,
    $end_date: timestamptz!, 
  ) {
    events_weekly_to_project(where: {
      project_id: { _in: $project_ids },
      event_type: { _in: $event_types },
      bucket_week: { _gte: $start_date, _lte: $end_date }
    }) {
      project_id
      event_type
      bucket_week
      amount
    }
  }
`);

const GET_EVENTS_MONTHLY_TO_PROJECT = gql(`
  query EventsMonthlyToProject(
    $project_ids: [String!],
    $event_types: [String!],
    $start_date: timestamptz!,
    $end_date: timestamptz!, 
  ) {
    events_monthly_to_project(where: {
      project_id: { _in: $project_ids },
      event_type: { _in: $event_types },
      bucket_month: { _gte: $start_date, _lte: $end_date }
    }) {
      project_id
      event_type
      bucket_month
      amount
    }
  }
`);

const GET_USERS_MONTHLY_TO_PROJECT = gql(`
  query UsersMonthlyToProject(
    $project_ids: [String!],
    $user_segment_types: [String!],
    $start_date: timestamptz!,
    $end_date: timestamptz!, 
  ) {
    users_monthly_to_project(where: {
      project_id: { _in: $project_ids },
      user_segment_type: { _in: $user_segment_types },
      bucket_month: { _gte: $start_date, _lte: $end_date }
    }) {
      project_id
      user_segment_type
      bucket_month
      amount
    }
  }
`);

const GET_EVENTS_DAILY_TO_ARTIFACT = gql(`
  query EventsDailyToArtifact(
    $artifact_ids: [String!],
    $event_types: [String!],
    $start_date: timestamptz!,
    $end_date: timestamptz!, 
  ) {
    events_daily_to_artifact(where: {
      artifact_id: { _in: $artifact_ids },
      event_type: { _in: $event_types },
      bucket_day: { _gte: $start_date, _lte: $end_date }
    }) {
      artifact_id
      event_type
      bucket_day
      amount
    }
  }
`);

const GET_EVENTS_WEEKLY_TO_ARTIFACT = gql(`
  query EventsWeeklyToArtifact(
    $artifact_ids: [String!],
    $event_types: [String!],
    $start_date: timestamptz!,
    $end_date: timestamptz!, 
  ) {
    events_weekly_to_artifact(where: {
      artifact_id: { _in: $artifact_ids },
      event_type: { _in: $event_types },
      bucket_week: { _gte: $start_date, _lte: $end_date }
    }) {
      artifact_id
      event_type
      bucket_week
      amount
    }
  }
`);

const GET_EVENTS_MONTHLY_TO_ARTIFACT = gql(`
  query EventsMonthlyToArtifact(
    $artifact_ids: [String!],
    $event_types: [String!],
    $start_date: timestamptz!,
    $end_date: timestamptz!, 
  ) {
    events_monthly_to_artifact(where: {
      artifact_id: { _in: $artifact_ids },
      event_type: { _in: $event_types },
      bucket_month: { _gte: $start_date, _lte: $end_date }
    }) {
      artifact_id
      event_type
      bucket_month
      amount
    }
  }
`);

export {
  GET_ALL_ARTIFACTS,
  GET_ARTIFACTS_BY_IDS,
  GET_ARTIFACT_BY_NAME,
  GET_ARTIFACT_IDS_BY_PROJECT_IDS,
  GET_ALL_PROJECTS,
  GET_PROJECTS_BY_IDS,
  GET_PROJECTS_BY_SLUGS,
  GET_ALL_COLLECTIONS,
  GET_COLLECTIONS_BY_IDS,
  GET_COLLECTIONS_BY_SLUGS,
  GET_COLLECTION_IDS_BY_PROJECT_IDS,
  GET_CODE_METRICS_BY_PROJECT,
  GET_ONCHAIN_METRICS_BY_PROJECT,
  GET_ALL_EVENT_TYPES,
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
};
