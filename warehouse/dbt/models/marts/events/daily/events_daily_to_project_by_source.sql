{# 
  All events daily to a project by source
#}
{{ 
  config(meta = {
    'sync_to_db': False
  }) 
}}

select
  project_id,
  event_source,
  event_type,
  TIMESTAMP_TRUNC(time, day) as bucket_day,
  SUM(amount) as amount
from {{ ref('int_events_to_project') }}
group by
  project_id,
  event_source,
  event_type,
  TIMESTAMP_TRUNC(time, day)
