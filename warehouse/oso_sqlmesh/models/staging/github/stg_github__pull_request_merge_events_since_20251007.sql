MODEL (
  name oso.stg_github__pull_request_merge_events_since_20251007,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column event_time,
    batch_size 365,
    batch_concurrency 3,
    lookback 14,
    forward_only true,
  ),
  start @github_events_v20251007_start_date,
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
)
SELECT DISTINCT
  pre.repo.id AS repository_id,
  pre.repo.name AS repository_name,
  'PULL_REQUEST_MERGED' AS "type",
  CAST(pre.payload ->> '$.pull_request.id' AS TEXT) AS id,
  -- TODO: Get the real details from the REST api
  pre.created_at AS event_time,
  CAST(NULL AS TIMESTAMP) AS merged_at,
  pre.created_at AS created_at,
  CAST(NULL AS TIMESTAMP) AS closed_at,
  CAST(pre.payload ->> '$.pull_request.user.id' AS INT) AS actor_id,
  pre.payload ->> '$.pull_request.user.login' AS actor_login,
  CAST(NULL AS VARCHAR) AS state,
  pre.payload ->> '$.pull_request.merge_commit_sha' AS merge_commit_sha,
  CAST(NULL AS INT) AS changed_files,
  CAST(NULL AS INT) AS additions,
  CAST(NULL AS INT) AS deletions,
  CAST(NULL AS DOUBLE) AS review_comments,
  CAST(NULL AS DOUBLE) AS comments,
  CAST(NULL AS VARCHAR) AS author_association,
  CAST(pre.payload ->> '$.number' AS BIGINT) AS "number"
FROM pull_request_events AS pre
WHERE
  pre.payload ->> '$.action' = 'closed'
  AND pre.created_at BETWEEN @start_dt AND @end_dt
