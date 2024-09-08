{# 
  All events weekly to an artifact
#}
{{ 
  config(meta = {
    'sync_to_db': False
  }) 
}}

select
  artifact_id,
  event_type,
  TIMESTAMP_TRUNC(bucket_day, week) as bucket_week,
  SUM(amount) as amount
from {{ ref('events_daily_to_artifact') }}
group by
  artifact_id,
  event_type,
  TIMESTAMP_TRUNC(bucket_day, week)
