{# 
  All events monthly to a collection by source
#}
{{ 
  config(meta = {
    'sync_to_db': False
  }) 
}}

select
  collection_id,
  event_source,
  event_type,
  TIMESTAMP_TRUNC(bucket_day, month) as bucket_month,
  SUM(amount) as amount
from {{ ref('events_daily_to_collection_by_source') }}
group by
  collection_id,
  event_source,
  event_type,
  TIMESTAMP_TRUNC(bucket_day, month)
