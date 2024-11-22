{{ 
  config(meta = {
    'sync_to_db': True,
    'order_by': [ 'artifact_source', 'metric', 'artifact_id', 'time' ]
  }) 
}}

select
  time,
  artifact_source,
  artifact_id,
  metric,
  amount
from {{ ref("int_point_in_time_from_sources") }}
