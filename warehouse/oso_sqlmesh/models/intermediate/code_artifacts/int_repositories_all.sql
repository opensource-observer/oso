MODEL (
  name oso.int_repositories_all,
  description 'All GitHub repositories identified from GH Archive',
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column first_commit_time,
    batch_size 365,
    batch_concurrency 1,
    lookback 31
  ),
  start @github_incremental_start,
  cron '@daily',
  dialect trino,
  partitioned_by DAY("first_commit_time"),
  grain (first_commit_time, artifact_id),
  columns (
    artifact_id TEXT,
    artifact_source_id TEXT,
    artifact_namespace TEXT,
    artifact_name TEXT,
    first_commit_time TIMESTAMP,
    last_commit_time TIMESTAMP
  ),
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := first_commit_time,
      no_gap_date_part := 'day'
    )
  )
);

WITH new_commits AS (
  SELECT
    to_artifact_id AS artifact_id,
    to_artifact_source_id AS artifact_source_id,
    to_artifact_namespace AS artifact_namespace,
    to_artifact_name AS artifact_name,
    time
  FROM oso.int_events__github
  WHERE event_type = 'COMMIT_CODE'
    AND time BETWEEN @start_dt AND @end_dt
),

existing_repos AS (
  SELECT
    artifact_id,
    artifact_source_id,
    artifact_namespace,
    artifact_name,
    first_commit_time,
    last_commit_time
  FROM oso.int_repositories_all
  WHERE first_commit_time < @start_dt
),

combined_data AS (
  SELECT
    artifact_id,
    artifact_source_id,
    artifact_namespace,
    artifact_name,
    time
  FROM new_commits
  
  UNION ALL
  
  SELECT
    artifact_id,
    artifact_source_id,
    artifact_namespace,
    artifact_name,
    first_commit_time AS time
  FROM existing_repos
  
  UNION ALL
  
  SELECT
    artifact_id,
    artifact_source_id,
    artifact_namespace,
    artifact_name,
    last_commit_time AS time
  FROM existing_repos
)

SELECT
  artifact_id,
  artifact_source_id,
  artifact_namespace,
  artifact_name,
  MIN(time) AS first_commit_time,
  MAX(time) AS last_commit_time
FROM combined_data
GROUP BY 1, 2, 3, 4