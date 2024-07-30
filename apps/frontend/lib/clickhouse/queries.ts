const GET_ALL_ARTIFACTS = `
  SELECT 
    artifact_id, 
    artifact_source, 
    artifact_namespace,
    artifact_name,
    artifact_url
  FROM artifacts_v1
`;

const GET_ARTIFACTS_BY_IDS = `
  SELECT
    artifact_id, 
    artifact_source, 
    artifact_namespace,
    artifact_name,
    artifact_url
  FROM artifacts_v1
  WHERE 
    artifact_id in {artifactIds: Array(String)}
`;

const GET_ARTIFACT_BY_SOURCE_NAMESPACE_NAME = `
  SELECT
    artifact_id, 
    artifact_source, 
    artifact_namespace,
    artifact_name,
    artifact_url
  FROM artifacts_v1
  WHERE 
    artifact_source = {artifactSource: String}
    and artifact_name = {artifactName: String} 
    and artifact_namespace {artifactNamespace: String}
`;

const GET_ARTIFACT_BY_SOURCE_NAME = `
  SELECT
    artifact_id, 
    artifact_source, 
    artifact_namespace,
    artifact_name,
    artifact_url
  FROM artifacts_v1
  WHERE 
    artifact_source = {artifactSource: String}
    and artifact_name = {artifactName: String}
`;

const GET_ARTIFACT_IDS_BY_PROJECT_IDS = `
  SELECT
    artifact_id
  FROM artifacts_by_project_v1
  WHERE
    project_id = {projectId: String}
`;

const GET_ALL_PROJECTS = `
  SELECT
    project_id,
    project_source,
    project_namespace,
    project_name,
    display_name
  FROM projects_v1
`;

const GET_PROJECTS_BY_IDS = `
  SELECT
    project_id,
    project_source,
    project_namespace,
    project_name,
    display_name,
    description
  FROM projects_v1
  WHERE 
    project_id in {projectIds: Array(String)}
`;

const GET_PROJECT_BY_NAME = `
  SELECT
    project_id,
    project_source,
    project_namespace,
    project_name,
    display_name,
    description
  FROM projects_v1
  WHERE
    project_name = {projectName: String}
`;

const GET_ALL_COLLECTIONS = `
  SELECT 
    collection_id, 
    collection_source, 
    collection_namespace, 
    collection_name, 
    display_name
  FROM 
    collections_v1;
`;

const GET_COLLECTIONS_BY_IDS = `
  SELECT 
    collection_id, 
    collection_source, 
    collection_namespace, 
    collection_name, 
    display_name, 
    description
  FROM 
    collections_v1
  WHERE 
    collection_id IN {collectionIds: Array(String)};
`;

const GET_COLLECTION_BY_NAME = `
  SELECT 
    collection_id, 
    collection_source, 
    collection_namespace, 
    collection_name, 
    display_name, 
    description
  FROM 
    collections_v1
  WHERE 
    collection_name = {collectionName: String};
`;

const GET_COLLECTION_IDS_BY_PROJECT_IDS = `
  SELECT 
    collection_id
  FROM 
    projects_by_collection_v1
  WHERE 
    project_id IN {projectIds: Array(String)};
`;

/**********************
 * METRICS
 **********************/

const GET_CODE_METRICS_BY_ARTIFACT = `
  SELECT 
    artifact_id,
    artifact_namespace,
    artifact_name,
    event_source,
    star_count,
    fork_count,
    contributor_count,
    contributor_count_6_months,
    new_contributor_count_6_months,
    fulltime_developer_average_6_months,
    active_developer_count_6_months,
    commit_count_6_months,
    opened_pull_request_count_6_months,
    merged_pull_request_count_6_months,
    opened_issue_count_6_months,
    closed_issue_count_6_months
  FROM 
    code_metrics_by_artifact_v0
  WHERE 
    artifact_id IN {artifactIds: Array(String)};
`;

const GET_CODE_METRICS_BY_PROJECT = `
  SELECT 
    project_id,
    project_source,
    project_namespace,
    project_name,
    display_name,
    event_source,
    active_developer_count_6_months,
    closed_issue_count_6_months,
    commit_count_6_months,
    contributor_count,
    contributor_count_6_months,
    first_commit_date,
    fork_count,
    fulltime_developer_average_6_months,
    last_commit_date,
    merged_pull_request_count_6_months,
    new_contributor_count_6_months,
    opened_issue_count_6_months,
    opened_pull_request_count_6_months,
    repository_count,
    star_count
  FROM 
    code_metrics_by_project_v1
  WHERE 
    project_id IN {projectIds: Array(String)};
`;

const GET_ONCHAIN_METRICS_BY_PROJECT = `
  SELECT 
    project_id,
    project_source,
    project_namespace,
    project_name,
    display_name,
    event_source,
    active_contract_count_90_days,
    address_count,
    address_count_90_days,
    days_since_first_transaction,
    gas_fees_sum,
    gas_fees_sum_6_months,
    high_activity_address_count_90_days,
    low_activity_address_count_90_days,
    medium_activity_address_count_90_days,
    multi_project_address_count_90_days,
    new_address_count_90_days,
    returning_address_count_90_days,
    transaction_count,
    transaction_count_6_months
  FROM 
    onchain_metrics_by_project_v1
  WHERE 
    project_id IN {projectIds: Array(String)};
`;

/**********************
 * EVENTS
 **********************/

const GET_ALL_EVENT_TYPES = `
  SELECT 
    event_type
  FROM 
    event_types_v1;
`;

const GET_EVENTS_DAILY_TO_COLLECTION = `
  SELECT 
    collection_id,
    event_type,
    bucket_day,
    amount
  FROM 
    events_daily_to_collection
  WHERE 
    collection_id IN {collectionIds: Array(String)} AND
    event_type IN {eventTypes: Array(String)} AND
    bucket_day BETWEEN {startDate: DateTime} AND {endDate: DateTime};
`;

const GET_EVENTS_WEEKLY_TO_COLLECTION = `
  SELECT 
    collection_id,
    event_type,
    bucket_week,
    amount
  FROM 
    events_weekly_to_collection
  WHERE 
    collection_id IN {collectionIds: Array(String)} AND
    event_type IN {eventTypes: Array(String)} AND
    bucket_week BETWEEN {startDate: DateTime} AND {endDate: DateTime};
`;

const GET_EVENTS_MONTHLY_TO_COLLECTION = `
  SELECT 
    collection_id,
    event_type,
    bucket_month,
    amount
  FROM 
    events_monthly_to_collection
  WHERE 
    collection_id IN {collectionIds: Array(String)} AND
    event_type IN {eventTypes: Array(String)} AND
    bucket_month BETWEEN {startDate: DateTime} AND {endDate: DateTime};
`;

const GET_EVENTS_DAILY_TO_PROJECT = `
  SELECT 
    project_id,
    event_type,
    bucket_day,
    amount
  FROM 
    events_daily_to_project
  WHERE 
    project_id IN {projectIds: Array(String)} AND
    event_type IN {eventTypes: Array(String)} AND
    bucket_day BETWEEN {startDate: DateTime} AND {endDate: DateTime};
`;

const GET_EVENTS_WEEKLY_TO_PROJECT = `
  SELECT 
    project_id,
    event_type,
    bucket_week,
    amount
  FROM 
    events_weekly_to_project
  WHERE 
    project_id IN {projectIds: Array(String)} AND
    event_type IN {eventTypes: Array(String)} AND
    bucket_week BETWEEN {startDate: DateTime} AND {endDate: DateTime};
`;

const GET_EVENTS_MONTHLY_TO_PROJECT = `
  SELECT 
    project_id,
    event_type,
    bucket_month,
    amount
  FROM 
    events_monthly_to_project
  WHERE 
    project_id IN {projectIds: Array(String)} AND
    event_type IN {eventTypes: Array(String)} AND
    bucket_month BETWEEN {startDate: DateTime} AND {endDate: DateTime};
`;

const GET_EVENTS_DAILY_TO_ARTIFACT = `
  SELECT 
    artifact_id,
    event_type,
    bucket_day,
    amount
  FROM 
    events_daily_to_artifact
  WHERE 
    artifact_id IN {artifactIds: Array(String)} AND
    event_type IN {eventTypes: Array(String)} AND
    bucket_day BETWEEN {startDate: DateTime} AND {endDate: DateTime};
`;

const GET_EVENTS_WEEKLY_TO_ARTIFACT = `
  SELECT 
    artifact_id,
    event_type,
    bucket_week,
    amount
  FROM 
    events_weekly_to_artifact
  WHERE 
    artifact_id IN {artifactIds: Array(String)} AND
    event_type IN {eventTypes: Array(String)} AND
    bucket_week BETWEEN {startDate: DateTime} AND {endDate: DateTime};
`;

const GET_EVENTS_MONTHLY_TO_ARTIFACT = `
  SELECT 
    artifact_id,
    event_type,
    bucket_month,
    amount
  FROM 
    events_monthly_to_artifact
  WHERE 
    artifact_id IN {artifactIds: Array(String)} AND
    event_type IN {eventTypes: Array(String)} AND
    bucket_month BETWEEN {startDate: DateTime} AND {endDate: DateTime};
`;

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
  GET_CODE_METRICS_BY_ARTIFACT,
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
};
