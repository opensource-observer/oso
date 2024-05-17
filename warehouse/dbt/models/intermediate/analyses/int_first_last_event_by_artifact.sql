{# 
  Summary stats for the first and last event for each artifact
#}

select
  project_id,
  from_artifact_id,
  to_artifact_id,
  event_source,
  event_type,
  MIN(bucket_day) as first_event_day,
  MAX(bucket_day) as last_event_day,
  COUNT(*) as event_count,
  SUM(amount) as amount
from {{ ref('int_events_daily_to_project') }}
group by
  project_id,
  from_artifact_id,
  to_artifact_id,
  event_source,
  event_type
