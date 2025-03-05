MODEL (
  name oso.int_superchain_s7_project_to_developer_graph,
  description "Maps relationships between trusted developers, onchain builder projects, and devtooling projects",
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column sample_date,
    batch_size 90,
    batch_concurrency 1,
    lookback 7
  ),
  start '2015-01-01',
  cron '@daily',
  partitioned_by DAY("sample_date"),
  grain (sample_date, developer_id, onchain_builder_project_id, devtooling_project_id)
);

WITH trusted_developers AS (
  SELECT
    developer_id,
    project_id AS onchain_builder_project_id,
    sample_date
  FROM oso.int_superchain_s7_trusted_developers
), eligible_devtooling_repos AS (
  SELECT
    repo_artifact_id,
    project_id AS devtooling_project_id,
    sample_date
  FROM oso.int_superchain_s7_devtooling_repo_eligibility
  WHERE
    is_eligible
), developer_events AS (
  SELECT
    trusted_developers.developer_id,
    trusted_developers.onchain_builder_project_id,
    eligible_devtooling_repos.devtooling_project_id,
    trusted_developers.sample_date,
    events.event_type,
    SUM(events.total_events) AS total_events,
    MIN(events.first_event) AS first_event,
    MAX(events.last_event) AS last_event
  FROM oso.int_developer_activity_by_repo AS events
  INNER JOIN trusted_developers
    ON events.developer_id = trusted_developers.developer_id
  INNER JOIN eligible_devtooling_repos
    ON events.repo_artifact_id = eligible_devtooling_repos.repo_artifact_id
  GROUP BY
    trusted_developers.developer_id,
    trusted_developers.onchain_builder_project_id,
    eligible_devtooling_repos.devtooling_project_id,
    trusted_developers.sample_date,
    events.event_type
), graph AS (
  SELECT
    developer_id,
    onchain_builder_project_id,
    devtooling_project_id,
    sample_date,
    MAX(event_type = 'STARRED') AS has_starred,
    MAX(event_type = 'FORKED') AS has_forked,
    MAX(event_type IN ('PULL_REQUEST_OPENED', 'PULL_REQUEST_MERGED', 'COMMIT_CODE')) AS has_code_contribution,
    MAX(event_type IN ('ISSUE_OPENED', 'ISSUE_COMMENTED')) AS has_issue_contribution,
    SUM(CASE WHEN event_type <> 'STARRED' THEN COALESCE(total_events, 1) ELSE 0 END) AS total_non_star_events,
    MIN(CASE WHEN event_type <> 'STARRED' THEN first_event ELSE NULL END) AS first_event,
    MAX(CASE WHEN event_type <> 'STARRED' THEN last_event ELSE NULL END) AS last_event
  FROM developer_events
  WHERE
    onchain_builder_project_id <> devtooling_project_id
  GROUP BY
    developer_id,
    onchain_builder_project_id,
    devtooling_project_id,
    sample_date
)
SELECT
  sample_date,
  developer_id,
  onchain_builder_project_id,
  devtooling_project_id,
  has_starred,
  has_forked,
  has_code_contribution,
  has_issue_contribution,
  total_non_star_events,
  first_event,
  last_event
FROM graph