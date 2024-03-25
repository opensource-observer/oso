WITH pull_request_events AS (
  SELECT *
  FROM {{ ref('stg_github__events') }} AS ghe
  WHERE ghe.type = "PullRequestEvent"
)

SELECT DISTINCT
  pre.repo.id AS repository_id,
  pre.repo.name AS repository_name,
  "PULL_REQUEST_MERGED" AS `type`,
  JSON_VALUE(pre.payload, "$.pull_request.id") AS id,
  PARSE_TIMESTAMP(
    "%Y-%m-%dT%H:%M:%E*SZ", JSON_VALUE(pre.payload, "$.pull_request.merged_at")
  ) AS created_at,
  CAST(JSON_VALUE(pre.payload, "$.pull_request.user.id") AS INTEGER)
    AS actor_id,
  JSON_VALUE(pre.payload, "$.pull_request.user.login") AS actor_login,
  JSON_VALUE(pre.payload, "$.pull_request.state") AS state,
  JSON_VALUE(pre.payload, "$.pull_request.merge_commit_sha") AS merge_commit_sha,
  JSON_VALUE(pre.payload, "$.pull_request.changed_files") AS changed_files,
  JSON_VALUE(pre.payload, "$.pull_request.additions") AS additions,
  JSON_VALUE(pre.payload, "$.pull_request.deletions") AS deletions,
  JSON_VALUE(pre.payload, "$.pull_request.review_comments") AS review_comments,
  JSON_VALUE(pre.payload, "$.pull_request.author_association") AS author_association
FROM pull_request_events AS pre
WHERE
  JSON_VALUE(pre.payload, "$.pull_request.merged_at") IS NOT NULL
  AND JSON_VALUE(pre.payload, "$.action") = "closed"
