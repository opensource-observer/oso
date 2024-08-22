{{ 
  config(meta = {
    'sync_to_db': True,
    'order_by': [ 'event_source', 'event_type', 'to_artifact_id', 'time' ]
  }) 
}}

select
  time,
  to_artifact_id,
  from_artifact_id,
  event_type,
  event_source_id,
  event_source,
  amount
from {{ ref('int_events') }}
