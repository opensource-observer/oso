MODEL (
  name oso.int_gharchive__repo_name_change_log,
  description 'Append-only log of repo_name change points (first-seen or rename). One row per change.',
  dialect trino,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column valid_from,
    batch_size 120,
    batch_concurrency 2,
    lookback @default_daily_incremental_lookback,
    forward_only true
  ),
  start @github_incremental_start,
  cron '@daily',
  partitioned_by MONTH("valid_from"),
  grain (repo_id, repo_name, valid_from),
  columns (
    repo_id BIGINT,
    repo_name TEXT,
    valid_from TIMESTAMP
  ),
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := valid_from,
      no_gap_date_part := 'day',
    ),
  ),
  tags (
    "github",
    "incremental",
  )
);

WITH last_known AS (
  SELECT repo_id, repo_name AS last_repo_name
  FROM (
    SELECT
      repo_id,
      repo_name,
      valid_from,
      row_number() OVER (PARTITION BY repo_id ORDER BY valid_from DESC) AS rn
    FROM oso.int_gharchive__repo_name_change_log
  ) t
  WHERE rn = 1
),
batch_events AS (
  SELECT
    repo_id,
    repo_name,
    event_time
  FROM oso.int_gharchive__github_events
  WHERE event_time BETWEEN @start_dt AND @end_dt
    AND repo_id IS NOT NULL
    AND repo_name IS NOT NULL
),
ordered AS (
  SELECT
    e.repo_id,
    e.repo_name,
    e.event_time,
    coalesce(
      lag(e.repo_name) OVER (PARTITION BY e.repo_id ORDER BY e.event_time),
      lk.last_repo_name
    ) AS prev_repo_name
  FROM batch_events e
  LEFT JOIN last_known lk
    ON e.repo_id = lk.repo_id
),
change_points AS (
  SELECT
    repo_id,
    repo_name,
    min(event_time) AS valid_from
  FROM ordered
  WHERE prev_repo_name IS NULL OR repo_name <> prev_repo_name
  GROUP BY repo_id, repo_name
)
SELECT
  repo_id,
  repo_name,
  valid_from
FROM change_points