{# 
  All events daily from a project
#}
{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

select
  e.project_id,
  e.event_type,
  TIMESTAMP_TRUNC(e.time, day) as bucket_day,
  SUM(e.amount) as amount
from {{ ref('int_events_from_project') }} as e
where e.project_id is not null
group by 1, 2, 3
