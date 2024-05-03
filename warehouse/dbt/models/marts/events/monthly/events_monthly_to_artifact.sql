{# 
  All events monthly to an artifact
#}
{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

select
  e.artifact_id,
  e.event_type,
  TIMESTAMP_TRUNC(e.bucket_day, month) as bucket_month,
  SUM(e.amount) as amount
from {{ ref('events_daily_to_artifact') }} as e
group by 1, 2, 3
