with pull_request_comment_events as (
  select
    ghe.id as id,
    ghe.created_at as created_at,
    ghe.repo.id as repository_id,
    ghe.repo.name as repository_name,
    ghe.actor.id as actor_id,
    ghe.actor.login as actor_login,
    'PULL_REQUEST_REVIEW_COMMENT' as `type`,
    JSON_VALUE(ghe.payload, '$.pull_request.number') as `number`
  from {{ ref('stg_github__events') }} as ghe
  where ghe.type = 'PullRequestReviewCommentEvent'
),

issue_comment_events as (
  select
    ghe.id as id,
    ghe.created_at as created_at,
    ghe.repo.id as repository_id,
    ghe.repo.name as repository_name,
    ghe.actor.id as actor_id,
    ghe.actor.login as actor_login,
    'ISSUE_COMMENT' as `type`,
    JSON_VALUE(ghe.payload, '$.issue.number') as `number`
  from {{ ref('stg_github__events') }} as ghe
  where ghe.type = 'IssueCommentEvent'
)

select * from pull_request_comment_events
union all
select * from issue_comment_events
