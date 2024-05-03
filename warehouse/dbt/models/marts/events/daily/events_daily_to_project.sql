{# 
  All events daily to a project
#}
{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

select
  e.project_id,
  e.event_type,
  TIMESTAMP_TRUNC(e.time, day) as bucket_day,
  SUM(e.amount) as amount
from {{ ref('int_events_to_project') }} as e
group by 1, 2, 3
