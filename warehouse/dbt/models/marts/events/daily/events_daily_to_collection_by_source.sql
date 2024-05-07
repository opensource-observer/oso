{# 
  All events daily to a collection by source
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
  TIMESTAMP_TRUNC(time, day) as bucket_day,
  SUM(amount) as amount
from {{ ref('int_events_to_collection') }}
group by
  collection_id,
  event_source,
  event_type,
  TIMESTAMP_TRUNC(time, day)
