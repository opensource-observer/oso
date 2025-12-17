MODEL (
  name oso.int_ddp_github_events_daily,
  description 'Raw GitHub Events from GitHub Archive since 2025-01-01, aggregated by day',
  dialect trino,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column bucket_day,
    batch_size 120,
    batch_concurrency 2,
    lookback @default_daily_incremental_lookback,
    forward_only true,
  ),
  start '2025-01-01',
  cron '@daily',
  partitioned_by (DAY("bucket_day"), "event_type"),
  grain (bucket_day, event_type, actor_id, repo_id),
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
    "ddp",
  )
);

SELECT
  DATE_TRUNC('DAY', event_time::DATE) AS bucket_day,
  actor_id,
  actor_login,
  repo_id,
  repo_name,
  CASE
    WHEN event_type = 'PushEvent' THEN 'COMMIT_CODE'
    WHEN event_type = 'WatchEvent' THEN 'STARRED'
    ELSE 'OTHER'
  END AS event_type,
  COUNT(*) AS amount
FROM oso.int_ddp_github_events
WHERE bucket_day BETWEEN @start_dt AND @end_dt
GROUP BY 1, 2, 3, 4, 5, 6