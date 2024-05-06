{# 
  Address stats by project
#}

select
  from_artifact_id as artifact_id,
  project_id,
  event_type,
  MIN(time) as first_transaction_time,
  MAX(time) as last_transaction_time,
  SUM(amount) as transaction_count
from {{ ref('int_events_to_project') }}
where
  event_type in (
    'CONTRACT_INVOCATION_DAILY_COUNT'
  )
group by
  from_artifact_id,
  project_id,
  event_type
