{# 
  All events to a project, cumulative (all time)
#}

select
  project_id,
  from_artifact_id,
  to_artifact_id,
  event_source,
  event_type,
  MIN(bucket_day) as first_event_time,
  MAX(bucket_day) as last_event_time,
  SUM(amount) as amount
from {{ ref('int_events_daily_to_project') }}
group by
  project_id,
  from_artifact_id,
  to_artifact_id,
  event_source,
  event_type
