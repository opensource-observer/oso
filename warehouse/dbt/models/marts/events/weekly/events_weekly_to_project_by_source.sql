{# 
  All events weekly to a project by source
#}

select
  project_id,
  event_source,
  event_type,
  TIMESTAMP_TRUNC(bucket_day, week) as bucket_week,
  SUM(amount) as amount
from {{ ref('events_daily_to_project_by_source') }}
group by
  project_id,
  event_source,
  event_type,
  TIMESTAMP_TRUNC(bucket_day, week)
