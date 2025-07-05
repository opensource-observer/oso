MODEL (
  name oso.stg_github__comments,
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
  )
);

WITH pull_request_comment_events AS (
  SELECT
    ghe.id AS id,
    STRPTIME(ghe.payload ->> '$.pull_request.updated_at', '%Y-%m-%dT%H:%M:%SZ') AS event_time,
    ghe.repo.id AS repository_id,
    ghe.repo.name AS repository_name,
    ghe.actor.id AS actor_id,
    ghe.actor.login AS actor_login,
    'PULL_REQUEST_REVIEW_COMMENT' AS "type",
    CAST(ghe.payload -> '$.pull_request.number' AS BIGINT) AS "number",
    STRPTIME(ghe.payload ->> '$.pull_request.created_at', '%Y-%m-%dT%H:%M:%SZ') AS created_at,
    STRPTIME(ghe.payload ->> '$.pull_request.merged_at', '%Y-%m-%dT%H:%M:%SZ') AS merged_at,
    STRPTIME(ghe.payload ->> '$.pull_request.closed_at', '%Y-%m-%dT%H:%M:%SZ') AS closed_at,
    ghe.payload ->> '$.pull_request.state' AS "state",
    CAST(ghe.payload -> '$.pull_request.comments' AS DOUBLE) AS comments
  FROM oso.stg_github__events AS ghe
  WHERE
    ghe.type = 'PullRequestReviewCommentEvent'
    and ghe.created_at BETWEEN @start_dt  - INTERVAL '1' DAY AND @end_dt + INTERVAL '1' DAY
    and STRPTIME(ghe.payload ->> '$.pull_request.updated_at', '%Y-%m-%dT%H:%M:%SZ') BETWEEN @start_dt AND @end_dt
), issue_comment_events AS (
  SELECT
    ghe.id AS id,
    -- the stg_github__events.created_at means the time the event was fired,
    -- but not the time the issue was updated (i.e. the time the IssuesEvent was created)
    -- so we need to use the issue.updated_at field from the payload
    STRPTIME(ghe.payload ->> '$.issue.updated_at', '%Y-%m-%dT%H:%M:%SZ') AS "event_time",
    ghe.repo.id AS repository_id,
    ghe.repo.name AS repository_name,
    ghe.actor.id AS actor_id,
    ghe.actor.login AS actor_login,
    'ISSUE_COMMENT' AS "type",
    CAST(ghe.payload -> '$.issue.number' AS INT) AS "number",
    STRPTIME(ghe.payload ->> '$.issue.created_at', '%Y-%m-%dT%H:%M:%SZ') AS created_at,
    NULL::TIMESTAMP AS merged_at,
    STRPTIME(ghe.payload ->> '$.issue.closed_at', '%Y-%m-%dT%H:%M:%SZ') AS closed_at,
    ghe.payload ->> '$.issue.state' AS "state",
    CAST(ghe.payload -> '$.issue.comments' AS DOUBLE) AS comments
  FROM oso.stg_github__events AS ghe
  WHERE
    ghe.type = 'IssueCommentEvent'
    and STRPTIME(ghe.payload ->> '$.issue.updated_at', '%Y-%m-%dT%H:%M:%SZ') BETWEEN @start_dt AND @end_dt
), all_events as (
  SELECT
    *
  FROM pull_request_comment_events
  UNION ALL
  SELECT
    *
  FROM issue_comment_events
)
SELECT
  id,
  event_time,
  repository_id,
  repository_name,
  actor_id,
  actor_login,
  "type",
  "number",
  created_at,
  merged_at,
  closed_at,
  "state",
  comments
FROM all_events
