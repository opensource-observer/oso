{# 
  All events daily to an artifact
#}
{{ 
  config(meta = {
    'sync_to_db': False
  }) 
}}

select
  to_artifact_id as artifact_id,
  event_type,
  TIMESTAMP_TRUNC(time, day) as bucket_day,
  SUM(amount) as amount
from {{ ref('int_events_to_project') }}
group by
  to_artifact_id,
  event_type,
  TIMESTAMP_TRUNC(time, day)
