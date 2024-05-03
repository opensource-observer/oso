{# 
  Address stats by project and network
#}

select
  e.project_id,
  e.from_namespace,
  e.from_id,
  e.bucket_day,
  e.amount,
  case
    when e.bucket_day = a.date_first_txn then 'NEW'
    else 'RETURNING'
  end as address_type
from {{ ref('int_user_events_daily_to_project') }} as e
left join {{ ref('int_addresses') }} as a
  on
    e.from_id = a.from_id
    and e.from_namespace = a.network
    and e.project_id = a.project_id
where
  e.event_type = 'CONTRACT_INVOCATION_DAILY_COUNT'
