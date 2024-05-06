{# 
  All events weekly to a project
#}
{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

select
  project_id,
  event_type,
  TIMESTAMP_TRUNC(bucket_day, week) as bucket_week,
  SUM(amount) as amount
from {{ ref('events_daily_to_project') }}
group by
  project_id,
  event_type,
  TIMESTAMP_TRUNC(bucket_day, week)
