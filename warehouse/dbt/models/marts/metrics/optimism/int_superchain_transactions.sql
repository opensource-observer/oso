{% set trailing_months = 6 %}

select
  time,
  from_artifact_id,
  to_artifact_id,
  sum(amount) as amount
from {{ ref('int_events__blockchain') }}
where
  event_type = 'CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT'
  and event_source in (
    'OPTIMISM', 'BASE', 'MODE', 'ZORA', 'METAL', 'FRAX'
  )
  and date(time) >= date_sub(
    current_date(), interval {{ trailing_months }} month
  )
  and from_artifact_id not in (
    select artifact_id from {{ ref('int_superchain_potential_bots') }}
  )
  and to_artifact_id not in (
    select artifact_id
    from {{ ref('int_artifacts_in_ossd_by_project') }}
    where artifact_type = 'WALLET'
  )
group by
  time,
  from_artifact_id,
  to_artifact_id
