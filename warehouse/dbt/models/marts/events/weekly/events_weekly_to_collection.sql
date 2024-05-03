{# 
  All events monthly to a collection
#}
{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

select
  e.collection_id,
  e.event_type,
  TIMESTAMP_TRUNC(e.bucket_day, week) as bucket_week,
  SUM(e.amount) as amount
from {{ ref('events_daily_to_collection') }} as e
group by 1, 2, 3
