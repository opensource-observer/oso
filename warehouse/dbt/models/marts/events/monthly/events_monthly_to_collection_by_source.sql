{# 
  All events monthly to a collection by source
#}
{{ 
  config(meta = {
    'sync_to_db': False
  }) 
}}

select
  e.collection_id,
  e.event_source,
  e.event_type,
  TIMESTAMP_TRUNC(e.bucket_day, month) as bucket_month,
  SUM(e.amount) as amount
from {{ ref('events_daily_to_collection_by_source') }} as e
group by 1, 2, 3, 4
