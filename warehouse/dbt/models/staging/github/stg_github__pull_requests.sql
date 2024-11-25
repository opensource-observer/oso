{#
  Turns all watch events into push events
#}

with pull_request_events as (
  select *
  from {{ ref('stg_github__events') }} as ghe
  where ghe.type = "PullRequestEvent"
)

select
  pre.id as id,
  pre.created_at as event_time,
  pre.repo.id as repository_id,
  pre.repo.name as repository_name,
  pre.actor.id as actor_id,
  pre.actor.login as actor_login,
  CONCAT("PULL_REQUEST_", UPPER(JSON_VALUE(pre.payload, "$.action")))
    as `type`,
  JSON_VALUE(pre.payload, "$.number") as `number`,
  PARSE_TIMESTAMP(
    "%Y-%m-%dT%H:%M:%E*SZ",
    JSON_VALUE(pre.payload, "$.pull_request.created_at")
  ) as created_at,
  PARSE_TIMESTAMP(
    "%Y-%m-%dT%H:%M:%E*SZ",
    JSON_VALUE(pre.payload, "$.pull_request.merged_at")
  ) as merged_at,
  PARSE_TIMESTAMP(
    "%Y-%m-%dT%H:%M:%E*SZ",
    JSON_VALUE(pre.payload, "$.pull_request.closed_at")
  ) as closed_at,
  JSON_VALUE(
    pre.payload,
    "$.pull_request.state"
  ) as `state`,
  JSON_VALUE(
    pre.payload,
    "$.pull_request.comments"
  ) as comments
from pull_request_events as pre
