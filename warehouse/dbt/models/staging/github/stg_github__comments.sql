with pull_request_comment_events as (
  select
    ghe.id as id,
    ghe.created_at as `event_time`,
    ghe.repo.id as repository_id,
    ghe.repo.name as repository_name,
    ghe.actor.id as actor_id,
    ghe.actor.login as actor_login,
    "PULL_REQUEST_REVIEW_COMMENT" as `type`,
    JSON_VALUE(ghe.payload, "$.pull_request.number") as `number`,
    JSON_VALUE(
      pre.payload,
      "$.pull_request.created_at"
    ) as created_at,
    JSON_VALUE(
      pre.payload,
      "$.pull_request.merged_at"
    ) as merged_at,
    JSON_VALUE(
      pre.payload,
      "$.pull_request.closed_at"
    ) as closed_at,
    JSON_VALUE(
      pre.payload,
      "$.pull_request.state"
    ) as `state`,
    JSON_VALUE(
      pre.payload,
      "$.pull_request.comments"
    ) as comments
  from {{ ref('stg_github__events') }} as ghe
  where ghe.type = "PullRequestReviewCommentEvent"
),

issue_comment_events as (
  select
    ghe.id as id,
    ghe.created_at as `event_time`,
    ghe.repo.id as repository_id,
    ghe.repo.name as repository_name,
    ghe.actor.id as actor_id,
    ghe.actor.login as actor_login,
    "ISSUE_COMMENT" as `type`,
    JSON_VALUE(ghe.payload, "$.issue.number") as `number`,
    JSON_VALUE(
      pre.payload,
      "$.issue.created_at"
    ) as created_at,
    NULL as merged_at, -- noqa
    JSON_VALUE(
      pre.payload,
      "$.issue.closed_at"
    ) as closed_at,
    JSON_VALUE(
      pre.payload,
      "$.issue.state"
    ) as `state`,
    JSON_VALUE(
      pre.payload,
      "$.issue.comments"
    ) as comments
  from {{ ref('stg_github__events') }} as ghe
  where ghe.type = "IssueCommentEvent"
)

select * from pull_request_comment_events
union all
select * from issue_comment_events
