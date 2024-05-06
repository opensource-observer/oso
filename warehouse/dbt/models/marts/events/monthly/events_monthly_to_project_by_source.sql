{# 
  All events monthly to a project by source
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
  TIMESTAMP_TRUNC(bucket_day, month) as bucket_month,
  SUM(amount) as amount
from {{ ref('events_daily_to_project_by_source') }}
group by
  project_id,
  event_source,
  event_type,
  TIMESTAMP_TRUNC(bucket_day, month)
