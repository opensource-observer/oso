MODEL (
  name oso.int_ddp_github_events,
  description 'Raw GitHub Events from GitHub Archive Since 2025-01-01',
  dialect trino,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column event_time,
    batch_size 120,
    batch_concurrency 2,
    lookback @default_daily_incremental_lookback,
    forward_only true,
  ),
  start '2025-01-01',
  cron '@daily',
  partitioned_by (DAY("event_time"), "event_type"),
  grain (event_time, actor_id, repo_id),
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := event_time,
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
  event_time,
  actor_id,
  actor_login,
  repo_id,
  repo_name,
  event_type,
FROM oso.int_gharchive__github_events
WHERE
  event_time BETWEEN @start_dt AND @end_dt
  AND event_type IN (
    'PushEvent',
    'IssuesEvent',
    'PullRequestEvent',
    'PullRequestReviewEvent',
    'PullRequestReviewCommentEvent',
    'WatchEvent',
    'ForkEvent'
  )