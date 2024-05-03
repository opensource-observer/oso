{# 
  All events monthly from a collection
#}
{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

select
  e.collection_id,
  e.event_type,
  TIMESTAMP_TRUNC(e.bucket_day, month) as bucket_month,
  SUM(e.amount) as amount
from {{ ref('events_daily_from_collection') }} as e
where e.collection_id is not null
group by 1, 2, 3
