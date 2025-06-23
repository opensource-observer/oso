MODEL (
  name oso.stg_github__pull_requests,
  description 'Turns all watch events into push events',
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column event_time,
    batch_size 90,
    batch_concurrency 3,
    lookback 31,
    forward_only true,
  ),
  dialect "duckdb",
  start @github_incremental_start,
  partitioned_by DAY(event_time),
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

WITH pull_request_events AS (
  SELECT
    *
  FROM oso.stg_github__events AS ghe
  WHERE
    ghe.type = 'PullRequestEvent'
    and STRPTIME(ghe.payload ->> '$.pull_request.updated_at', '%Y-%m-%dT%H:%M:%SZ') BETWEEN @start_dt AND @end_dt
)
SELECT
  pre.id AS id,
  STRPTIME(pre.payload ->> '$.pull_request.updated_at', '%Y-%m-%dT%H:%M:%SZ') AS event_time,
  pre.repo.id AS repository_id,
  pre.repo.name AS repository_name,
  pre.actor.id AS actor_id,
  pre.actor.login AS actor_login,
  CONCAT('PULL_REQUEST_', UPPER(pre.payload ->> '$.action')) AS "type",
  CAST(pre.payload -> '$.number' AS BIGINT) AS "number",
  STRPTIME(pre.payload ->> '$.pull_request.created_at', '%Y-%m-%dT%H:%M:%SZ') AS created_at,
  STRPTIME(pre.payload ->> '$.pull_request.merged_at', '%Y-%m-%dT%H:%M:%SZ') AS merged_at,
  STRPTIME(pre.payload ->> '$.pull_request.closed_at', '%Y-%m-%dT%H:%M:%SZ') AS closed_at,
  pre.payload ->> '$.pull_request.state' AS "state",
  CAST(pre.payload -> '$.pull_request.comments' AS DOUBLE) AS comments,
  CAST(pre.payload ->> '$.pull_request.author_association' AS VARCHAR) AS author_association
FROM pull_request_events AS pre
