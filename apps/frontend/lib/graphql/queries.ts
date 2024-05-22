import { gql } from "../__generated__/gql";

// Max TTL on Hasura is 300 seconds
// https://hasura.io/docs/latest/caching/caching-config/#controlling-cache-lifetime/

/**********************
 * ARTIFACT
 **********************/

const GET_ALL_ARTIFACTS = gql(`
  query Artifacts @cached (ttl: 300) {
    artifacts_v1 {
      artifact_id
      artifact_source
      artifact_namespace
      artifact_name
      artifact_url
    }
  }
`);

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

const GET_ARTIFACT_BY_SOURCE_NAMESPACE_NAME = gql(`
  query ArtifactBySourceNamespaceName($artifact_source: String!, $artifact_namespace: String!, $artifact_name: String!) @cached(ttl: 300) {
    artifacts_v1(where: { artifact_source: { _eq: $artifact_source }, artifact_namespace: { _eq: $artifact_namespace }, artifact_name: { _eq: $artifact_name } }) {
      artifact_id
      artifact_source
      artifact_namespace
      artifact_name
      artifact_url
    }
  }
`);

const GET_ARTIFACT_BY_SOURCE_NAME = gql(`
  query ArtifactBySourceName($artifact_source: String!, $artifact_name: String!) @cached(ttl: 300) {
    artifacts_v1(where: { artifact_source: { _eq: $artifact_source }, artifact_name: { _eq: $artifact_name } }) {
      artifact_id
      artifact_source
      artifact_namespace
      artifact_name
      artifact_url
    }
  }
`);

const GET_ARTIFACT_IDS_BY_PROJECT_IDS = gql(`
  query ArtifactIdsByProjectIds($project_ids: [String!]) @cached(ttl: 300) {
    artifacts_by_project_v1(where: { project_id: { _in: $project_ids }}) {
      artifact_id
    }
  }
`);

/**********************
 * PROJECT
 **********************/

const GET_ALL_PROJECTS = gql(`
  query Projects @cached(ttl: 300) {
    projects_v1 {
      project_id
      project_source
      project_namespace
      project_name
      display_name
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

const GET_PROJECT_BY_NAME = gql(`
  query ProjectByName($project_name: String!) @cached(ttl: 300) {
    projects_v1(where: { project_name: { _eq: $project_name } }) {
      project_id
      project_source
      project_namespace
      project_name
      display_name
      description
    }
  }
`);

/**********************
 * COLLECTION
 **********************/

const GET_ALL_COLLECTIONS = gql(`
  query Collections @cached(ttl: 300) {
    collections_v1 {
      collection_id
      collection_source
      collection_namespace
      collection_name
      display_name
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

const GET_COLLECTION_BY_NAME = gql(`
  query CollectionByName($collection_name: String!) @cached(ttl: 300) {
    collections_v1(where: { collection_name: { _eq: $collection_name } }) {
      collection_id
      collection_source
      collection_namespace
      collection_name
      display_name
      description
    }
  }
`);

const GET_COLLECTION_IDS_BY_PROJECT_IDS = gql(`
  query CollectionIdsByProjectIds($project_ids: [String!]) @cached(ttl: 300) {
    projects_by_collection_v1(where: { project_id: { _in: $project_ids }}) {
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
    code_metrics_by_project_v1(where: {
      project_id: { _in: $project_ids },
    }) {
      project_id
      project_source
      project_namespace
      project_name
      display_name
      event_source
      active_developer_count_6_months
      closed_issue_count_6_months
      commit_count_6_months
      contributor_count
      contributor_count_6_months
      first_commit_date
      fork_count
      fulltime_developer_average_6_months
      last_commit_date
      merged_pull_request_count_6_months
      new_contributor_count_6_months
      opened_issue_count_6_months
      opened_pull_request_count_6_months
      repository_count
      star_count
    }
  }
`);

const GET_ONCHAIN_METRICS_BY_PROJECT = gql(`
  query OnchainMetricsByProject(
    $project_ids: [String!],
  ) {
    onchain_metrics_by_project_v1(where: {
      project_id: { _in: $project_ids },
    }) {
      project_id
      project_source
      project_namespace
      project_name
      display_name
      event_source
      active_contract_count_90_days
      address_count
      address_count_90_days
      days_since_first_transaction
      gas_fees_sum
      gas_fees_sum_6_months
      high_activity_address_count_90_days
      low_activity_address_count_90_days
      medium_activity_address_count_90_days
      multi_project_address_count_90_days
      new_address_count_90_days
      returning_address_count_90_days
      transaction_count
      transaction_count_6_months
    }
  }
`);

/**********************
 * EVENTS
 **********************/

const GET_ALL_EVENT_TYPES = gql(`
  query GetAllEventTypes @cached(ttl: 300) {
    event_types_v1 {
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

/**
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
*/

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
  GET_ARTIFACT_BY_SOURCE_NAMESPACE_NAME,
  GET_ARTIFACT_BY_SOURCE_NAME,
  GET_ARTIFACT_IDS_BY_PROJECT_IDS,
  GET_ALL_PROJECTS,
  GET_PROJECTS_BY_IDS,
  GET_PROJECT_BY_NAME,
  GET_ALL_COLLECTIONS,
  GET_COLLECTIONS_BY_IDS,
  GET_COLLECTION_BY_NAME,
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
  //GET_USERS_MONTHLY_TO_PROJECT,
};
