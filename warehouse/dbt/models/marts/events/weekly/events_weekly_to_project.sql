{# 
  All events weekly to a project
#}
{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

select
  e.project_id,
  e.event_type,
  TIMESTAMP_TRUNC(e.bucket_day, week) as bucket_week,
  SUM(e.amount) as amount
from {{ ref('events_daily_to_project') }} as e
group by 1, 2, 3
