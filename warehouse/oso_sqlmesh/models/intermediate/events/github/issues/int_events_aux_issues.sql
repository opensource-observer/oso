MODEL (
  name oso.int_events_aux_issues,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column time,
    batch_size 365,
    batch_concurrency 2,
    lookback 31,
    forward_only true
  ),
  start '2015-01-01',
  cron '@daily',
  partitioned_by (DAY("time"), "event_type"),
  grain (time, event_type, event_source, from_artifact_id, to_artifact_id),
  dialect duckdb,
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := time,
      no_gap_date_part := 'day',
    ),
  ),
  tags (
    "incremental"
  )
);

WITH github_comments AS (
  /* noqa: ST06 */
  SELECT
    "event_time" AS "time",
    type AS event_type,
    id::TEXT AS event_source_id,
    'GITHUB' AS event_source,
    STR_SPLIT(REPLACE(repository_name, '@', ''), '/')[@array_index(1)] AS to_name,
    STR_SPLIT(REPLACE(repository_name, '@', ''), '/')[@array_index(0)] AS to_namespace,
    'REPOSITORY' AS to_type,
    repository_id::TEXT AS to_artifact_source_id,
    actor_login AS from_name,
    actor_login AS from_namespace,
    'GIT_USER' AS from_type,
    actor_id::TEXT AS from_artifact_source_id,
    "number" AS issue_number,
    created_at,
    merged_at,
    closed_at,
    comments
  FROM oso.stg_github__comments
  WHERE
    event_time BETWEEN @start_dt AND @end_dt
), github_issues AS (
  /* noqa: ST06 */
  SELECT
    event_time AS "time",
    type AS event_type,
    id::TEXT AS event_source_id,
    'GITHUB' AS event_source,
    STR_SPLIT(REPLACE(repository_name, '@', ''), '/')[@array_index(1)] AS to_name,
    STR_SPLIT(REPLACE(repository_name, '@', ''), '/')[@array_index(0)] AS to_namespace,
    'REPOSITORY' AS to_type,
    repository_id::TEXT AS to_artifact_source_id,
    actor_login AS from_name,
    actor_login AS from_namespace,
    'GIT_USER' AS from_type,
    actor_id::TEXT AS from_artifact_source_id,
    "number" AS issue_number,
    created_at,
    NULL::TIMESTAMP AS merged_at,
    closed_at,
    comments
  FROM oso.stg_github__issues
  WHERE
    event_time BETWEEN @start_dt AND @end_dt
), github_pull_requests AS (
  /* noqa: ST06 */
  SELECT
    event_time AS "time",
    type AS event_type,
    id::TEXT AS event_source_id,
    'GITHUB' AS event_source,
    STR_SPLIT(REPLACE(repository_name, '@', ''), '/')[@array_index(1)] AS to_name,
    STR_SPLIT(REPLACE(repository_name, '@', ''), '/')[@array_index(0)] AS to_namespace,
    'REPOSITORY' AS to_type,
    repository_id::TEXT AS to_artifact_source_id,
    actor_login AS from_name,
    actor_login AS from_namespace,
    'GIT_USER' AS from_type,
    actor_id::TEXT AS from_artifact_source_id,
    "number" AS issue_number,
    created_at,
    merged_at,
    closed_at,
    comments
  FROM oso.stg_github__pull_requests
  WHERE
    event_time BETWEEN @start_dt AND @end_dt
), github_pull_request_merge_events AS (
  /* noqa: ST06 */
  SELECT
    event_time AS "time",
    type AS event_type,
    id::TEXT AS event_source_id,
    'GITHUB' AS event_source,
    STR_SPLIT(REPLACE(repository_name, '@', ''), '/')[@array_index(1)] AS to_name,
    STR_SPLIT(REPLACE(repository_name, '@', ''), '/')[@array_index(0)] AS to_namespace,
    'REPOSITORY' AS to_type,
    repository_id::TEXT AS to_artifact_source_id,
    actor_login AS from_name,
    actor_login AS from_namespace,
    'GIT_USER' AS from_type,
    actor_id::TEXT AS from_artifact_source_id,
    "number" AS issue_number,
    created_at,
    merged_at,
    closed_at,
    comments
  FROM oso.stg_github__pull_request_merge_events
  WHERE
    event_time BETWEEN @start_dt AND @end_dt
), issue_events AS (
  SELECT
    time,
    event_type,
    event_source_id,
    event_source,
    @oso_entity_id(event_source, to_namespace, to_name) AS to_artifact_id,
    @oso_entity_id(event_source, from_namespace, from_name) AS from_artifact_id,
    issue_number,
    created_at,
    merged_at,
    closed_at,
    comments
  FROM (
    SELECT
      *
    FROM github_issues
    UNION ALL
    SELECT
      *
    FROM github_pull_requests
    UNION ALL
    SELECT
      *
    FROM github_pull_request_merge_events
    UNION ALL
    SELECT
      *
    FROM github_comments
  )
)
SELECT
  time,
  to_artifact_id,
  from_artifact_id,
  @oso_id(event_source, to_artifact_id, issue_number) AS issue_id,
  issue_number,
  created_at,
  merged_at,
  closed_at,
  comments,
  UPPER(event_type) AS event_type,
  event_source_id::TEXT AS event_source_id,
  UPPER(event_source) AS event_source
FROM issue_events
