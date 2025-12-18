MODEL (
  name oso.int_gharchive__developer_activities,
  description 'Developer activities from GitHub Archive',
  dialect trino,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column bucket_day,
    batch_size 120,
    batch_concurrency 2,
    lookback @default_daily_incremental_lookback,
    on_destructive_change warn,
    forward_only true,
  ),
  start @github_incremental_start,
  cron '@daily',
  partitioned_by DAY("bucket_day"),
  grain (bucket_day, actor_id, repo_id),
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

SELECT
  DATE_TRUNC('DAY', event_time::DATE) AS bucket_day,
  actor_id,
  repo_id,
  COUNT(*) AS num_events
FROM oso.int_gharchive__github_events
WHERE
  event_time BETWEEN @start_dt AND @end_dt
  AND event_type IN ('PushEvent', 'PullRequestEvent')
GROUP BY 1, 2, 3