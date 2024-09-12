import _ from "lodash";

// Not ideal, but this was a hack to get the data type out of the sql by hand
// easily. Will refactor on a subsequent change.
function define<T>(sql: string, rowType: T): { sql: string; rowType: T } {
  return {
    sql: sql,
    rowType: rowType,
  };
}

const artifactResponse = {
  artifact_id: "",
  artifact_source: "",
  artifact_namespace: "",
  artifact_name: "",
  artifact_url: "",
};

const GET_ALL_ARTIFACTS = define(
  `
  SELECT 
    artifact_id, 
    artifact_source, 
    artifact_namespace,
    artifact_name,
    artifact_url
  FROM artifacts_v1
`,
  artifactResponse,
);

const GET_ARTIFACTS_BY_IDS = define(
  `
  SELECT
    artifact_id, 
    artifact_source, 
    artifact_namespace,
    artifact_name,
    artifact_url
  FROM artifacts_v1
  WHERE 
    artifact_id in {artifactIds: Array(String)}
`,
  artifactResponse,
);

const GET_ARTIFACT_BY_SOURCE_NAMESPACE_NAME = define(
  `
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
    and artifact_namespace = {artifactNamespace: String}
`,
  artifactResponse,
);

const GET_ARTIFACT_BY_SOURCE_NAME = define(
  `
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
`,
  artifactResponse,
);

const GET_ARTIFACT_IDS_BY_PROJECT_IDS = define(
  `
  SELECT
    artifact_id
  FROM artifacts_by_project_v1
  WHERE
    project_id = {projectId: String}
`,
  { artifact_id: "" },
);

const projectResponse = {
  project_id: "",
  project_source: "",
  project_namespace: "",
  project_name: "",
  display_name: "",
};

const projectResponseWithDescription = _.merge(projectResponse, {
  description: "",
});

const GET_ALL_PROJECTS = define(
  `
  SELECT
    project_id,
    project_source,
    project_namespace,
    project_name,
    display_name
  FROM projects_v1
`,
  projectResponse,
);

const GET_PROJECTS_BY_IDS = define(
  `
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
`,
  projectResponseWithDescription,
);

const GET_PROJECT_BY_NAME = define(
  `
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
`,
  projectResponseWithDescription,
);

const GET_PROJECT_IDS_BY_COLLECTION_NAME = define(
  `
  SELECT
    project_id,
  FROM projects_by_collection_v1
  WHERE
    collection_source = {collectionSource: String}
    AND collection_namespace = {collectionNamespace: String}
    AND collection_name = {collectionName: String};
  `,
  { project_id: "" },
);

const collectionResponse = {
  collection_id: "",
  collection_source: "",
  collection_namespace: "",
  collection_name: "",
  display_name: "",
};

const collectionResponseWithDescription = _.merge(collectionResponse, {
  description: "",
});

const GET_ALL_COLLECTIONS = define(
  `
  SELECT 
    collection_id, 
    collection_source, 
    collection_namespace, 
    collection_name, 
    display_name
  FROM 
    collections_v1;
`,
  collectionResponse,
);

const GET_COLLECTIONS_BY_IDS = define(
  `
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
`,
  collectionResponseWithDescription,
);

const GET_COLLECTION_BY_NAME = define(
  `
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
    collection_source = {collectionSource: String}
    AND collection_namespace = {collectionNamespace: String}
    AND collection_name = {collectionName: String};
`,
  collectionResponseWithDescription,
);

const GET_COLLECTION_IDS_BY_PROJECT_IDS = define(
  `
  SELECT 
    collection_id
  FROM 
    projects_by_collection_v1
  WHERE 
    project_id IN {projectIds: Array(String)};
`,
  { collection_id: "" },
);

/**********************
 * METRICS
 **********************/

const metricResponse = {
  metric_id: "",
  metric_source: "",
  metric_namespace: "",
  metric_name: "",
  display_name: "",
};

const metricResponseWithDescription = _.merge(metricResponse, {
  description: "",
});

const GET_METRIC_BY_NAME = define(
  `
  SELECT 
    metric_id, 
    metric_source, 
    metric_namespace, 
    metric_name, 
    display_name, 
    description
  FROM 
    metrics.metrics_v0
  WHERE 
    metric_source = {metricSource: String}
    AND metric_namespace = {metricNamespace: String}
    AND metric_name = {metricName: String};
`,
  metricResponseWithDescription,
);

const GET_CODE_METRICS_BY_ARTIFACT = define(
  `
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
`,
  {
    artifact_id: "",
    artifact_namespace: "",
    artifact_name: "",
    event_source: "",
    star_count: 0,
    fork_count: 0,
    contributor_count: 0,
    contributor_count_6_months: 0,
    new_contributor_count_6_months: 0,
    fulltime_developer_average_6_months: 0,
    active_developer_count_6_months: 0,
    commit_count_6_months: 0,
    opened_pull_request_count_6_months: 0,
    merged_pull_request_count_6_months: 0,
    opened_issue_count_6_months: 0,
    closed_issue_count_6_months: 0,
  },
);

const GET_CODE_METRICS_BY_PROJECT = define(
  `
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
`,
  {
    project_id: "",
    project_source: "",
    project_namespace: "",
    project_name: "",
    display_name: "",
    event_source: "",
    active_developer_count_6_months: 0,
    closed_issue_count_6_months: 0,
    commit_count_6_months: 0,
    contributor_count: 0,
    contributor_count_6_months: 0,
    first_commit_date: "",
    fork_count: 0,
    fulltime_developer_average_6_months: 0,
    last_commit_date: "",
    merged_pull_request_count_6_months: 0,
    new_contributor_count_6_months: 0,
    opened_issue_count_6_months: 0,
    opened_pull_request_count_6_months: 0,
    repository_count: 0,
    star_count: 0,
  },
);

const GET_ONCHAIN_METRICS_BY_PROJECT = define(
  `
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
`,
  {
    project_id: "",
    project_source: "",
    project_namespace: "",
    project_name: "",
    display_name: "",
    event_source: "",
    active_contract_count_90_days: 0,
    address_count: 0,
    address_count_90_days: 0,
    days_since_first_transaction: 0,
    gas_fees_sum: 0,
    gas_fees_sum_6_months: 0,
    high_activity_address_count_90_days: 0,
    low_activity_address_count_90_days: 0,
    medium_activity_address_count_90_days: 0,
    multi_project_address_count_90_days: 0,
    new_address_count_90_days: 0,
    returning_address_count_90_days: 0,
    transaction_count: 0,
    transaction_count_6_months: 0,
  },
);

/**********************
 * EVENTS
 **********************/

const GET_ALL_EVENT_TYPES = define(
  `
  SELECT 
    event_type
  FROM 
    event_types_v1;
`,
  { event_type: "" },
);

const GET_EVENTS_DAILY_TO_COLLECTION = define(
  `
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
`,
  {
    collection_id: "",
    event_type: "",
    bucket_day: "",
    amount: 0,
  },
);

const GET_EVENTS_WEEKLY_TO_COLLECTION = define(
  `
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
`,
  {
    collection_id: "",
    event_type: "",
    bucket_week: "",
    amount: 0,
  },
);

const GET_EVENTS_MONTHLY_TO_COLLECTION = define(
  `
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
`,
  {
    collection_id: "",
    event_type: "",
    bucket_month: "",
    amount: 0,
  },
);

const GET_EVENTS_DAILY_TO_PROJECT = define(
  `
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
`,
  {
    project_id: "",
    event_type: "",
    bucket_day: "",
    amount: 0,
  },
);

const GET_EVENTS_WEEKLY_TO_PROJECT = define(
  `
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
`,
  {
    project_id: "",
    event_type: "",
    bucket_week: "",
    amount: 0,
  },
);

const GET_EVENTS_MONTHLY_TO_PROJECT = define(
  `
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
`,
  {
    project_id: "",
    event_type: "",
    bucket_month: "",
    amount: 0,
  },
);

const GET_EVENTS_DAILY_TO_ARTIFACT = define(
  `
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
`,
  {
    artifact_id: "",
    event_type: "",
    bucket_day: "",
    amount: 0,
  },
);

const GET_EVENTS_WEEKLY_TO_ARTIFACT = define(
  `
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
`,
  {
    artifact_id: "",
    event_type: "",
    bucket_week: "",
    amount: 0,
  },
);

const GET_EVENTS_MONTHLY_TO_ARTIFACT = define(
  `
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
`,
  {
    artifact_id: "",
    event_type: "",
    bucket_month: "",
    amount: 0,
  },
);

export {
  GET_ALL_ARTIFACTS,
  GET_ARTIFACTS_BY_IDS,
  GET_ARTIFACT_BY_SOURCE_NAMESPACE_NAME,
  GET_ARTIFACT_BY_SOURCE_NAME,
  GET_ARTIFACT_IDS_BY_PROJECT_IDS,
  GET_ALL_PROJECTS,
  GET_PROJECTS_BY_IDS,
  GET_PROJECT_BY_NAME,
  GET_PROJECT_IDS_BY_COLLECTION_NAME,
  GET_ALL_COLLECTIONS,
  GET_COLLECTIONS_BY_IDS,
  GET_COLLECTION_BY_NAME,
  GET_COLLECTION_IDS_BY_PROJECT_IDS,
  GET_METRIC_BY_NAME,
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
