{# 
  All events monthly to a collection
#}
{{ 
  config(meta = {
    'sync_to_db': False
  }) 
}}

select
  collection_id,
  event_type,
  TIMESTAMP_TRUNC(bucket_day, week) as bucket_week,
  SUM(amount) as amount
from {{ ref('events_daily_to_collection') }}
group by
  collection_id,
  event_type,
  TIMESTAMP_TRUNC(bucket_day, week)
