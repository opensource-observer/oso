{# 
  All events to a project, bucketed by day
#}

select
  project_id,
  from_artifact_id,
  to_artifact_id,
  event_source,
  event_type,
  TIMESTAMP_TRUNC(time, day) as bucket_day,
  SUM(amount) as amount
from {{ ref('int_events_to_project') }}
group by
  project_id,
  from_artifact_id,
  to_artifact_id,
  event_source,
  event_type,
  TIMESTAMP_TRUNC(time, day)
order by bucket_day
limit 10