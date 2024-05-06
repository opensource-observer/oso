{#
  WIP: Still in Development
  Count the number of contracts deployed by a project
  that have more than 100 users
#}

{% set min_trusted_users = 100 %}

with users_by_contract as (
  select
    to_artifact_id as artifact_id,
    COUNT(distinct from_id) as num_users
  from {{ ref('int_events_with_artifact_id') }}
  where
    from_artifact_id in (
      select user_id
      from {{ ref('int_users') }}
    )
    and event_type = 'CONTRACT_INVOCATION_DAILY_COUNT'
  group by 1
),

valid_contracts as (
  select artifact_id
  from users_by_contract
  where num_users >= {{ min_trusted_users }}
)

select
  a.project_id,
  COUNT(distinct a.artifact_id) as amount
from valid_contracts as v
left join {{ ref('artifacts_by_project_v1') }} as a
  on v.artifact_id = a.artifact_id
group by 1
