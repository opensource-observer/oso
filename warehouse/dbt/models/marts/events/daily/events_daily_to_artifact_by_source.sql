{# 
  All events daily to an artifact by source
#}
{{ 
  config(meta = {
    'sync_to_db': False
  }) 
}}

select
  e.to_id as artifact_id,
  e.from_namespace,
  e.event_type,
  TIMESTAMP_TRUNC(e.time, day) as bucket_day,
  SUM(e.amount) as amount
from {{ ref('int_events_to_project') }} as e
group by 1, 2, 3, 4
