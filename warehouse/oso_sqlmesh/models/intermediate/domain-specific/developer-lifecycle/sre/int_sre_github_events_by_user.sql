MODEL (
  name oso.int_sre_github_events_by_user,
  description 'Events from GitHub Archive by SRE GitHub Users',
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
  )
);

SELECT
  events.event_time,
  users.github_handle AS user_name,
  events.repo_name AS repo_name,
  events.event_type AS event_type,
  events.actor_id AS github_user_id,
  events.repo_id AS github_repo_id  
FROM oso.int_sre_github_events AS events
JOIN oso.int_sre_github_users AS users
  ON events.actor_login = users.github_handle
WHERE events.event_time BETWEEN @start_dt AND @end_dt