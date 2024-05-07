{# 
  All events daily to a project
#}
{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

select
  project_id,
  event_type,
  TIMESTAMP_TRUNC(time, day) as bucket_day,
  SUM(amount) as amount
from {{ ref('int_events_to_project') }}
group by
  project_id,
  event_type,
  TIMESTAMP_TRUNC(time, day)
