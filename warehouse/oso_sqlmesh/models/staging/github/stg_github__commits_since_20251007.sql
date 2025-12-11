MODEL (
  name oso.stg_github__commits_since_20251007,
  description 'Turns all push events into their commit objects (version after 2025-10-07)',
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column created_at,
    batch_size 90,
    batch_concurrency 3,
    lookback @default_daily_incremental_lookback,
    forward_only true,
  ),
  start @github_events_v20251007_start_date,
  partitioned_by DAY(created_at),
  dialect trino,
  audits (
    no_gaps(
      time_column := created_at,
      no_gap_date_part := 'day',
    ),
  ),
  tags (
    "incremental"
  )
);

SELECT
  ghpe.created_at AS created_at,
  ghpe.repository_id AS repository_id,
  ghpe.repository_name AS repository_name,
  ghpe.push_id AS push_id,
  ghpe.ref AS ref,
  ghpe.actor_id AS actor_id,
  ghpe.actor_login AS actor_login,
  ghpe.head AS sha,
  CAST(NULL AS VARCHAR) AS author_email,
  CAST(NULL AS VARCHAR) AS author_name,
  TRUE AS is_distinct,
  CAST(NULL AS VARCHAR) AS api_url
FROM oso.stg_github__push_events_since_20251007 AS ghpe
WHERE ghpe.created_at BETWEEN @start_dt AND @end_dt
