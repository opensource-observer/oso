{{ 
  config(meta = {
    'sync_to_db': True,
    'order_by': [ 'event_source', 'event_type', 'to_artifact_id', 'time' ]
  }) 
}}

select
  time,
  artifact_source,
  artifact_id,
  metric,
  amount
from {{ ref("int_point_in_time_from_sources") }}
