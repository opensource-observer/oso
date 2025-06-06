MODEL (
  name oso.int_events_daily__github_with_zero_filling,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column bucket_day,
    batch_size 365,
    batch_concurrency 2,
    lookback 31,
    forward_only true,
  ),
  start @github_incremental_start,
  cron '@daily',
  partitioned_by (DAY("bucket_day"), "event_type"),
  grain (bucket_day, event_type, event_source, from_artifact_id, to_artifact_id),
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := bucket_day,
      no_gap_date_part := 'day',
    ),
  ),
  tags (
    "github",
    "incremental",
  )
);

WITH all_dates AS (
  @date_spine('day', @start_dt, @end_dt)
),
all_distinct_artifacts AS (
  SELECT DISTINCT
    from_artifact_id,
    to_artifact_id,
    event_source,
    event_type
  FROM oso.int_events_daily__github
  WHERE bucket_day BETWEEN @start_dt AND @end_dt
),
repository_first_commits AS (
  SELECT
    artifact_id,
    DATE_TRUNC('DAY', first_commit_time) AS first_commit_date
  FROM oso.int_first_last_commit_to_github_repository
),
date_artifact_combinations AS (
  SELECT
    all_dates.date_day AS bucket_day,
    all_distinct_artifacts.from_artifact_id,
    all_distinct_artifacts.to_artifact_id,
    all_distinct_artifacts.event_source,
    all_distinct_artifacts.event_type
  FROM all_dates
  CROSS JOIN all_distinct_artifacts
  LEFT JOIN repository_first_commits AS to_repo_commits
    ON all_distinct_artifacts.to_artifact_id = to_repo_commits.artifact_id
  WHERE 
    to_repo_commits.first_commit_date IS NOT NULL
    AND all_dates.date_day >= to_repo_commits.first_commit_date
)
SELECT
  DATE_TRUNC('DAY', date_artifact_combinations.bucket_day) AS bucket_day,
  date_artifact_combinations.from_artifact_id::VARCHAR AS from_artifact_id,
  date_artifact_combinations.to_artifact_id::VARCHAR AS to_artifact_id,
  date_artifact_combinations.event_source::VARCHAR AS event_source,
  date_artifact_combinations.event_type::VARCHAR AS event_type,
  COALESCE(actual_events.amount, 0.0)::DOUBLE AS amount
FROM date_artifact_combinations
LEFT JOIN oso.int_events_daily__github AS actual_events
  ON date_artifact_combinations.bucket_day = actual_events.bucket_day
  AND date_artifact_combinations.from_artifact_id = actual_events.from_artifact_id
  AND date_artifact_combinations.to_artifact_id = actual_events.to_artifact_id
  AND date_artifact_combinations.event_source = actual_events.event_source
  AND date_artifact_combinations.event_type = actual_events.event_type
WHERE date_artifact_combinations.bucket_day BETWEEN @start_dt AND @end_dt
