{# 
  All events weekly to an artifact
#}
{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

select
  to_artifact_id,
  event_type,
  TIMESTAMP_TRUNC(bucket_day, week) as bucket_week,
  SUM(amount) as amount
from {{ ref('events_daily_to_artifact') }}
group by
  to_artifact_id,
  event_type,
  TIMESTAMP_TRUNC(bucket_day, week)
