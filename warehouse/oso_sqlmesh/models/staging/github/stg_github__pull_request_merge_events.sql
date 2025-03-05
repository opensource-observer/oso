MODEL (
  name oso.stg_github__pull_request_merge_events,
  kind FULL
);

WITH pull_request_events AS (
  SELECT
    *
  FROM @oso_source('bigquery.oso.stg_github__events') AS ghe
  WHERE
    ghe.type = 'PullRequestEvent'
)
SELECT DISTINCT
  pre.repo.id AS repository_id,
  pre.repo.name AS repository_name,
  'PULL_REQUEST_MERGED' AS "type",
  CAST(pre.payload -> '$.pull_request.id' AS TEXT) AS id,
  STRPTIME(pre.payload ->> '$.pull_request.merged_at', '%Y-%m-%dT%H:%M:%SZ') AS event_time,
  STRPTIME(pre.payload ->> '$.pull_request.merged_at', '%Y-%m-%dT%H:%M:%SZ') AS merged_at,
  STRPTIME(pre.payload ->> '$.pull_request.created_at', '%Y-%m-%dT%H:%M:%SZ') AS created_at,
  STRPTIME(pre.payload ->> '$.pull_request.closed_at', '%Y-%m-%dT%H:%M:%SZ') AS closed_at,
  CAST(pre.payload -> '$.pull_request.user.id' AS INT) AS actor_id,
  pre.payload ->> '$.pull_request.user.login' AS actor_login,
  pre.payload ->> '$.pull_request.state' AS state,
  pre.payload ->> '$.pull_request.merge_commit_sha' AS merge_commit_sha,
  CAST(pre.payload -> '$.pull_request.changed_files' AS INT) AS changed_files,
  CAST(pre.payload -> '$.pull_request.additions' AS INT) AS additions,
  CAST(pre.payload -> '$.pull_request.deletions' AS INT) AS deletions,
  CAST(pre.payload -> '$.pull_request.review_comments' AS DOUBLE) AS review_comments,
  CAST(pre.payload -> '$.pull_request.comments' AS DOUBLE) AS comments,
  pre.payload ->> '$.pull_request.author_association' AS author_association,
  CAST(pre.payload -> '$.number' AS BIGINT) AS "number"
FROM pull_request_events AS pre
WHERE
  NOT (
    pre.payload ->> '$.pull_request.merged_at'
  ) IS NULL
  AND (
    pre.payload ->> '$.action'
  ) = 'closed'