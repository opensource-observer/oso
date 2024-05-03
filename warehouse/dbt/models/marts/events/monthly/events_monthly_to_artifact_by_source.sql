{# 
  All events monthly to an artifact by source
#}
{{ 
  config(meta = {
    'sync_to_db': False
  }) 
}}

select
  e.artifact_id,
  e.from_namespace,
  e.event_type,
  TIMESTAMP_TRUNC(e.bucket_day, month) as bucket_month,
  SUM(e.amount) as amount
from {{ ref('events_daily_to_artifact_by_source') }} as e
group by 1, 2, 3, 4
