{# 
  All events monthly to a collection
#}
{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

select
  collection_id,
  event_type,
  TIMESTAMP_TRUNC(bucket_day, month) as bucket_month,
  SUM(amount) as amount
from {{ ref('events_daily_to_collection') }}
group by
  collection_id,
  event_type,
  TIMESTAMP_TRUNC(bucket_day, month)
