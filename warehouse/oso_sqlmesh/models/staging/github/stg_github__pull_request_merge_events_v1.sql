MODEL (
  name oso.stg_github__pull_request_merge_events_v1,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column event_time,
    batch_size 365,
    batch_concurrency 3,
    lookback 14,
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
  )
);

WITH pull_request_events AS (
  SELECT
    *
  FROM oso.stg_github__events AS ghe
  WHERE
    ghe.type = 'PullRequestEvent'
    -- We cast a wider net of pull request events to ensure we capture any
    -- random changes for a single pullrequest in a given time range
    and ghe.created_at BETWEEN @start_dt  - INTERVAL '15' DAY AND @end_dt + INTERVAL '1' DAY
    and ghe.created_at < '2025-10-07'
)
SELECT DISTINCT
  pre.repo.id AS repository_id,
  pre.repo.name AS repository_name,
  'PULL_REQUEST_MERGED' AS "type",
  CAST(pre.payload ->> '$.pull_request.id' AS TEXT) AS id,
  STRPTIME(pre.payload ->> '$.pull_request.updated_at', '%Y-%m-%dT%H:%M:%SZ') AS event_time,
  STRPTIME(pre.payload ->> '$.pull_request.merged_at', '%Y-%m-%dT%H:%M:%SZ') AS merged_at,
  STRPTIME(pre.payload ->> '$.pull_request.created_at', '%Y-%m-%dT%H:%M:%SZ') AS created_at,
  STRPTIME(pre.payload ->> '$.pull_request.closed_at', '%Y-%m-%dT%H:%M:%SZ') AS closed_at,
  CAST(pre.payload ->> '$.pull_request.user.id' AS INT) AS actor_id,
  pre.payload ->> '$.pull_request.user.login' AS actor_login,
  pre.payload ->> '$.pull_request.state' AS state,
  pre.payload ->> '$.pull_request.merge_commit_sha' AS merge_commit_sha,
  CAST(pre.payload ->> '$.pull_request.changed_files' AS INT) AS changed_files,
  CAST(pre.payload ->> '$.pull_request.additions' AS INT) AS additions,
  CAST(pre.payload ->> '$.pull_request.deletions' AS INT) AS deletions,
  CAST(pre.payload ->> '$.pull_request.review_comments' AS DOUBLE) AS review_comments,
  CAST(pre.payload ->> '$.pull_request.comments' AS DOUBLE) AS comments,
  pre.payload ->> '$.pull_request.author_association' AS author_association,
  CAST(pre.payload ->> '$.number' AS BIGINT) AS "number"
FROM pull_request_events AS pre
WHERE
  NOT (
    pre.payload ->> '$.pull_request.merged_at'
  ) IS NULL
  AND (
    pre.payload ->> '$.action'
  ) = 'closed'
  AND STRPTIME(pre.payload ->> '$.pull_request.updated_at', '%Y-%m-%dT%H:%M:%SZ') BETWEEN @start_dt AND @end_dt
