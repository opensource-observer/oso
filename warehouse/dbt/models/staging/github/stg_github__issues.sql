{#
  Turns all watch events into push events
#}

with issue_events as (
  select *
  from {{ ref('stg_github__events') }} as ghe
  where ghe.type = "IssuesEvent"
)

select
  ie.id as id,
  ie.created_at as event_time,
  ie.repo.id as repository_id,
  ie.repo.name as repository_name,
  ie.actor.id as actor_id,
  ie.actor.login as actor_login,
  CONCAT("ISSUE_", UPPER(JSON_VALUE(ie.payload, "$.action"))) as `type`,
  JSON_VALUE(ie.payload, "$.issue.number") as `number`,
  PARSE_TIMESTAMP(
    "%Y-%m-%dT%H:%M:%E*SZ",
    JSON_VALUE(ie.payload, "$.issue.created_at")
  ) as created_at,
  PARSE_TIMESTAMP(
    "%Y-%m-%dT%H:%M:%E*SZ",
    JSON_VALUE(ie.payload, "$.issue.closed_at")
  ) as closed_at,
  JSON_VALUE(
    ie.payload,
    "$.issue.state"
  ) as `state`,
  JSON_VALUE(
    ie.payload,
    "$.issue.comments"
  ) as comments
from issue_events as ie
