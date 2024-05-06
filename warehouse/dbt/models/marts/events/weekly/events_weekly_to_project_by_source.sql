{# 
  All events weekly to a project by source
#}

select
  e.project_id,
  e.event_source,
  e.event_type,
  TIMESTAMP_TRUNC(e.bucket_day, week) as bucket_week,
  SUM(e.amount) as amount
from {{ ref('events_daily_to_project_by_source') }} as e
group by 1, 2, 3, 4
