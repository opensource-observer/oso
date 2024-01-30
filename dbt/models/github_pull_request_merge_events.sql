WITH pull_request_events AS (
    SELECT * 
    FROM {{ ref('github_events') }} as ghe
    WHERE ghe.type = "PullRequestEvent"
)
SELECT DISTINCT
  JSON_VALUE(pre.payload, "$.pull_request.id") as id,
  PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%E*SZ', JSON_VALUE(pre.payload, "$.pull_request.merged_at")) AS created_at,
  pre.repo.id AS repository_id,
  pre.repo.name AS repository_name,
  JSON_VALUE(pre.payload, "$.pull_request.user.id") AS actor_id,
  JSON_VALUE(pre.payload, "$.pull_request.user.login") AS actor_login,
  "PULL_REQUEST_MERGED" AS type,
  JSON_VALUE(pre.payload, "$.pull_request.state") as state,
  JSON_VALUE(pre.payload, "$.pull_request.merge_commit_sha") as merge_commit_sha,
FROM pull_request_events AS pre
WHERE JSON_VALUE(pre.payload, "$.pull_request.merged_at") IS NOT NULL AND JSON_VALUE(pre.payload, "$.action") = "closed"