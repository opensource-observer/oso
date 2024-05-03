{# 
  Address stats by project and network
#}

select
  from_id,
  from_namespace as network,
  project_id,
  MIN(bucket_day) as date_first_txn,
  MAX(bucket_day) as date_last_txn,
  SUM(amount) as count_events
from {{ ref('int_user_events_daily_to_project') }}
where event_type = 'CONTRACT_INVOCATION_DAILY_COUNT'
group by 1, 2, 3
