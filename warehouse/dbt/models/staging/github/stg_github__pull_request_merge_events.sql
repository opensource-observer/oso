with pull_request_events as (
  select *
  from {{ ref('stg_github__events') }} as ghe
  where ghe.type = "PullRequestEvent"
)

select distinct
  pre.repo.id as repository_id,
  pre.repo.name as repository_name,
  "PULL_REQUEST_MERGED" as `type`,
  JSON_VALUE(pre.payload, "$.pull_request.id") as id,
  PARSE_TIMESTAMP(
    "%Y-%m-%dT%H:%M:%E*SZ",
    JSON_VALUE(pre.payload, "$.pull_request.merged_at")
  ) as event_time,
  PARSE_TIMESTAMP(
    "%Y-%m-%dT%H:%M:%E*SZ",
    JSON_VALUE(pre.payload, "$.pull_request.merged_at")
  ) as merged_at,
  PARSE_TIMESTAMP(
    "%Y-%m-%dT%H:%M:%E*SZ",
    JSON_VALUE(pre.payload, "$.pull_request.created_at")
  ) as created_at,
  PARSE_TIMESTAMP(
    "%Y-%m-%dT%H:%M:%E*SZ",
    JSON_VALUE(pre.payload, "$.pull_request.closed_at")
  ) as closed_at,
  CAST(JSON_VALUE(pre.payload, "$.pull_request.user.id") as INTEGER)
    as actor_id,
  JSON_VALUE(
    pre.payload, "$.pull_request.user.login"
  ) as actor_login,
  JSON_VALUE(
    pre.payload, "$.pull_request.state"
  ) as state,
  JSON_VALUE(
    pre.payload, "$.pull_request.merge_commit_sha"
  ) as merge_commit_sha,
  JSON_VALUE(
    pre.payload, "$.pull_request.changed_files"
  ) as changed_files,
  JSON_VALUE(
    pre.payload, "$.pull_request.additions"
  ) as additions,
  JSON_VALUE(
    pre.payload, "$.pull_request.deletions"
  ) as deletions,
  JSON_VALUE(
    pre.payload, "$.pull_request.review_comments"
  ) as review_comments,
  JSON_VALUE(
    pre.payload, "$.pull_request.comments"
  ) as comments,
  JSON_VALUE(
    pre.payload, "$.pull_request.author_association"
  ) as author_association,
  JSON_VALUE(pre.payload, "$.number") as `number`
from pull_request_events as pre
where
  JSON_VALUE(pre.payload, "$.pull_request.merged_at") is not null
  and JSON_VALUE(pre.payload, "$.action") = "closed"
