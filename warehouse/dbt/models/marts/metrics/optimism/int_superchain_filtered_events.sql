{% set trailing_days = 180 %}

select
  events.time,
  events.from_artifact_id,
  events.to_artifact_id,
  artifacts.project_id as to_project_id,
  events.event_type,
  events.event_source,
  events.amount
from {{ ref('int_events__blockchain') }} as events
inner join {{ ref('artifacts_by_project_v1') }} as artifacts
  on events.to_artifact_id = artifacts.artifact_id
where
  events.event_type in (
    'CONTRACT_INVOCATION_DAILY_L2_GAS_USED', 'CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT'
  )
  and events.event_source in (
    'OPTIMISM', 'BASE', 'MODE', 'ZORA', 'METAL', 'FRAX'
  )
  and date(events.time) >= date_sub(
    current_date(), interval {{ trailing_days }} day
  )
  and events.from_artifact_id not in (
    select artifact_id from {{ ref('int_superchain_potential_bots') }}
  )
  and events.to_artifact_id not in (
    select artifact_id
    from {{ ref('int_artifacts_in_ossd_by_project') }}
    where artifact_type = 'WALLET'
  )
