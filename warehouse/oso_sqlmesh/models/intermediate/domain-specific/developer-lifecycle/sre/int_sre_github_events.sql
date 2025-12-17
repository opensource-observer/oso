MODEL (
  name oso.int_sre_github_events,
  description 'Raw GitHub Events from GitHub Archive',
  dialect trino,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column event_time,
    batch_size 120,
    batch_concurrency 2,
    lookback @default_daily_incremental_lookback,
    forward_only true,
  ),
  start '2020-01-01',
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
  ),
  enabled false
);

SELECT
  created_at AS event_time,
  actor.id AS actor_id,
  LOWER(actor.login) AS actor_login,
  repo.id AS repo_id,
  LOWER(repo.name) AS repo_name,
  type AS event_type,
FROM oso.stg_github__events
WHERE
  created_at BETWEEN @start_dt AND @end_dt
  AND type IN (
    'PushEvent',
    'IssuesEvent',
    'PullRequestEvent',
    'PullRequestReviewEvent',
    'PullRequestReviewCommentEvent',
    'WatchEvent',
    'ForkEvent'
  )