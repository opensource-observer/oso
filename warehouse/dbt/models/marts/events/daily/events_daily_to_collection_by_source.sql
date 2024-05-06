{# 
  All events daily to a collection by source
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
  TIMESTAMP_TRUNC(e.time, day) as bucket_day,
  SUM(e.amount) as amount
from {{ ref('int_events_to_collection') }} as e
group by 1, 2, 3, 4
