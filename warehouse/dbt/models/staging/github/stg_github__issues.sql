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
  ie.created_at as created_at,
  ie.repo.id as repository_id,
  ie.repo.name as repository_name,
  ie.actor.id as actor_id,
  ie.actor.login as actor_login,
  CONCAT("ISSUE_", UPPER(JSON_VALUE(ie.payload, "$.action"))) as `type`
from issue_events as ie
