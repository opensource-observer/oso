MODEL (
  name oso.stg_github__issues,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column event_time,
    batch_size 90,
    batch_concurrency 3,
    lookback 31,
    forward_only true,
  ),
  start @github_incremental_start,
  partitioned_by DAY(event_time),
  dialect duckdb,
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := event_time,
      no_gap_date_part := 'day',
    ),
  ),
  tags (
    "incremental"
  )
);

WITH issue_events AS (
  SELECT
  *
  FROM oso.stg_github__events AS ghe
  WHERE
    ghe.type = 'IssuesEvent'
    and ghe.created_at BETWEEN @start_dt AND @end_dt
)
SELECT
  ie.id AS id,
  ie.created_at AS event_time,
  ie.repo.id AS repository_id,
  ie.repo.name AS repository_name,
  ie.actor.id AS actor_id,
  ie.actor.login AS actor_login,
  CONCAT('ISSUE_', UPPER(ie.payload ->> '$.action')) AS "type",
  CAST(ie.payload -> '$.issue.number' AS BIGINT) AS "number",
  STRPTIME(ie.payload ->> '$.issue.created_at', '%Y-%m-%dT%H:%M:%SZ') AS created_at,
  STRPTIME(ie.payload ->> '$.issue.closed_at', '%Y-%m-%dT%H:%M:%SZ') AS closed_at,
  ie.payload ->> '$.issue.state' AS "state",
  CAST(ie.payload -> '$.issue.comments' AS DOUBLE) AS comments
FROM issue_events AS ie