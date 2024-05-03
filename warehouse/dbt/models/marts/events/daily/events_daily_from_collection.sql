{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

select
  e.collection_id,
  e.event_type,
  TIMESTAMP_TRUNC(e.time, day) as bucket_day,
  SUM(e.amount) as amount
from {{ ref('int_events_from_collection') }} as e
where e.collection_id is not null
group by 1, 2, 3
