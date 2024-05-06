{# 
  Address stats by project and network
#}

select
  int_events_to_project.project_id,
  int_events_to_project.from_artifact_id,
  int_events_to_project.event_source,
  int_events_to_project.amount,
  DATE_TRUNC(int_events_to_project.time, day) as bucket_day,
  case
    when
      int_events_to_project.time
      = int_addresses_to_project.first_transaction_time
      then 'NEW'
    else 'RETURNING'
  end as address_type
from {{ ref('int_events_to_project') }}
left join {{ ref('int_addresses_to_project') }}
  on
    int_events_to_project.from_artifact_id
    = int_addresses_to_project.artifact_id
    and int_events_to_project.project_id = int_addresses_to_project.project_id
where
  int_events_to_project.event_type = 'CONTRACT_INVOCATION_DAILY_COUNT'
