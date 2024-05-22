{# 
  All events monthly to an artifact
#}
{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

select
  artifact_id,
  event_type,
  TIMESTAMP_TRUNC(bucket_day, month) as bucket_month,
  SUM(amount) as amount
from {{ ref('events_daily_to_artifact') }}
group by
  artifact_id,
  event_type,
  TIMESTAMP_TRUNC(bucket_day, month)
