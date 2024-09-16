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
  pre.created_at as created_at,
  pre.repo.id as repository_id,
  pre.repo.name as repository_name,
  pre.actor.id as actor_id,
  pre.actor.login as actor_login,
  CONCAT("PULL_REQUEST_", UPPER(JSON_VALUE(pre.payload, "$.action")))
    as `type`,
  JSON_VALUE(ie.payload, "$.number") as `number`
from pull_request_events as pre
